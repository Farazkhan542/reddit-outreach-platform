import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select

from app.api.deps import DB, Admin, Current
from app.models import Lead, LeadAssignment, LeadStatus, RedditAccount, User
from app.schemas import AssignIn, LeadOut
from app.services.distribution import create_assignment

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
async def list_leads(current: Current, db: DB, status_filter: LeadStatus | None = None, limit: int = 100):
    """Admins see every lead in the org; members see their assigned leads plus unclaimed qualified ones."""
    query = select(Lead).where(Lead.org_id == current.org_id)
    if not current.is_admin:
        query = query.outerjoin(LeadAssignment, LeadAssignment.lead_id == Lead.id).where(
            or_(
                LeadAssignment.user_id == current.user.id,
                (LeadAssignment.id.is_(None)) & (Lead.status == LeadStatus.qualified),
            )
        )
    if status_filter:
        query = query.where(Lead.status == status_filter)
    return (await db.scalars(query.order_by(Lead.created_at.desc()).limit(limit))).all()


async def _get_lead(db, org_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    lead = await db.scalar(select(Lead).where(Lead.id == lead_id, Lead.org_id == org_id))
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return lead


@router.post("/{lead_id}/claim", response_model=LeadOut)
async def claim_lead(lead_id: uuid.UUID, current: Current, db: DB):
    lead = await _get_lead(db, current.org_id, lead_id)
    if await db.scalar(select(LeadAssignment).where(LeadAssignment.lead_id == lead.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "lead already assigned")
    account = await db.scalar(select(RedditAccount).where(RedditAccount.user_id == current.user.id))
    await create_assignment(db, lead, current.user.id, account.id if account else None, current.user.id)
    await db.commit()
    return lead


@router.post("/{lead_id}/assign", response_model=LeadOut)
async def assign(lead_id: uuid.UUID, data: AssignIn, current: Admin, db: DB):
    lead = await _get_lead(db, current.org_id, lead_id)
    assignee = await db.scalar(select(User).where(User.id == data.user_id, User.org_id == current.org_id))
    if assignee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not in this org")
    account = await db.scalar(select(RedditAccount).where(RedditAccount.user_id == assignee.id))
    await create_assignment(db, lead, assignee.id, account.id if account else None, current.user.id)
    await db.commit()
    return lead


@router.post("/{lead_id}/converted", response_model=LeadOut)
async def mark_converted(lead_id: uuid.UUID, current: Current, db: DB):
    lead = await _get_lead(db, current.org_id, lead_id)
    lead.status = LeadStatus.converted
    await db.commit()
    return lead
