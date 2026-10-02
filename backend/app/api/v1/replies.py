import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DB, Current, CurrentUser
from app.models import LeadAssignment, Reply, ReplyStatus
from app.schemas import ReplyEditIn, ReplyOut
from app.services.sender import SendError, send_reply

router = APIRouter(prefix="/replies", tags=["replies"])


@router.get("", response_model=list[ReplyOut])
async def list_replies(current: Current, db: DB, status_filter: ReplyStatus | None = ReplyStatus.pending_review):
    """The human review queue. Members only see drafts for leads assigned to them."""
    query = select(Reply).where(Reply.org_id == current.org_id)
    if not current.is_admin:
        query = query.join(LeadAssignment, LeadAssignment.lead_id == Reply.lead_id).where(
            LeadAssignment.user_id == current.user.id
        )
    if status_filter:
        query = query.where(Reply.status == status_filter)
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
async def approve_reply(reply_id: uuid.UUID, current: Current, db: DB, send_now: bool = True):
    """Human approval gate. Logs the approver, then posts from the assigned member's account."""
    reply = await _get_reviewable(db, current, reply_id)
    if reply.status != ReplyStatus.pending_review:
        raise HTTPException(status.HTTP_409_CONFLICT, f"reply is {reply.status.value}")
    reply.status = ReplyStatus.approved
    reply.approved_by_id = current.user.id
    reply.approved_at = datetime.now(timezone.utc)
    await db.commit()

    if send_now:
        try:
            await send_reply(db, reply)
        except SendError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
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
