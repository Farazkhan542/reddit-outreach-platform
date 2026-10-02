import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DB, Current, CurrentUser
from app.models import Lead, LeadAssignment, LeadStatus, RedditAccount, Reply, ReplyStatus
from app.schemas import MarkPostedIn, ReplyEditIn, ReplyOut

router = APIRouter(prefix="/replies", tags=["replies"])


@router.get("", response_model=list[ReplyOut])
async def list_replies(
    current: Current,
    db: DB,
    status_filter: list[ReplyStatus] = Query([ReplyStatus.pending_review, ReplyStatus.approved]),
):
    """The review queue: drafts to review plus approved replies waiting to be posted manually.
    Members only see replies for leads assigned to them."""
    query = select(Reply).where(Reply.org_id == current.org_id)
    if not current.is_admin:
        query = query.join(LeadAssignment, LeadAssignment.lead_id == Reply.lead_id).where(
            LeadAssignment.user_id == current.user.id
        )
    if status_filter:
        query = query.where(Reply.status.in_(status_filter))
    return (await db.scalars(query.order_by(Reply.created_at.desc()))).all()


async def _get_reviewable(db, current: CurrentUser, reply_id: uuid.UUID) -> Reply:
    reply = await db.scalar(select(Reply).where(Reply.id == reply_id, Reply.org_id == current.org_id))
    if reply is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not current.is_admin:
        assignment = await db.scalar(select(LeadAssignment).where(LeadAssignment.lead_id == reply.lead_id))
        if assignment is None or assignment.user_id != current.user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "lead is not assigned to you")
    return reply


@router.patch("/{reply_id}", response_model=ReplyOut)
async def edit_reply(reply_id: uuid.UUID, data: ReplyEditIn, current: Current, db: DB):
    reply = await _get_reviewable(db, current, reply_id)
    if reply.status != ReplyStatus.pending_review:
        raise HTTPException(status.HTTP_409_CONFLICT, "only pending drafts can be edited")
    reply.final_body = data.final_body
    await db.commit()
    return reply


@router.post("/{reply_id}/approve", response_model=ReplyOut)
async def approve_reply(reply_id: uuid.UUID, current: Current, db: DB):
    """Human approval gate. The app does not post anything: the reviewer copies the
    approved text and posts it themselves on reddit.com, then calls /mark-posted."""
    reply = await _get_reviewable(db, current, reply_id)
    if reply.status != ReplyStatus.pending_review:
        raise HTTPException(status.HTTP_409_CONFLICT, f"reply is {reply.status.value}")
    reply.status = ReplyStatus.approved
    reply.approved_by_id = current.user.id
    reply.approved_at = datetime.now(timezone.utc)
    await db.commit()
    return reply


@router.post("/{reply_id}/mark-posted", response_model=ReplyOut)
async def mark_posted(reply_id: uuid.UUID, data: MarkPostedIn, current: Current, db: DB):
    """Records that the reviewer posted the approved reply manually on reddit.com."""
    reply = await _get_reviewable(db, current, reply_id)
    if reply.status != ReplyStatus.approved:
        raise HTTPException(status.HTTP_409_CONFLICT, "only approved replies can be marked as posted")
    now = datetime.now(timezone.utc)
    reply.status = ReplyStatus.posted
    reply.posted_by_id = current.user.id
    reply.posted_at = now
    reply.posted_url = data.posted_url

    lead = await db.get(Lead, reply.lead_id)
    lead.status = LeadStatus.contacted
    account = await db.scalar(select(RedditAccount).where(RedditAccount.user_id == current.user.id))
    if account:
        account.last_action_at = now
    await db.commit()
    return reply


@router.post("/{reply_id}/reject", response_model=ReplyOut)
async def reject_reply(reply_id: uuid.UUID, current: Current, db: DB):
    reply = await _get_reviewable(db, current, reply_id)
    if reply.status != ReplyStatus.pending_review:
        raise HTTPException(status.HTTP_409_CONFLICT, f"reply is {reply.status.value}")
    reply.status = ReplyStatus.rejected
    reply.approved_by_id = current.user.id
    await db.commit()
    return reply
