from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import DB, Admin
from app.models import Lead, LeadStatus, Reply, ReplyStatus
from app.schemas import AnalyticsOut
from app.services.pipeline import PipelineResult, run_pipeline_for_org

router = APIRouter(tags=["pipeline"])


@router.post("/pipeline/run", response_model=PipelineResult)
async def run_pipeline_now(current: Admin, db: DB):
    """Runs Scout -> Classifier -> Drafter once, inline. Celery Beat runs the same thing on a schedule."""
    return await run_pipeline_for_org(db, current.org_id)


@router.get("/analytics", response_model=AnalyticsOut)
async def analytics(current: Admin, db: DB):
    async def count(model, *where):
        return await db.scalar(select(func.count()).select_from(model).where(model.org_id == current.org_id, *where))

    qualified_states = [LeadStatus.qualified, LeadStatus.assigned, LeadStatus.contacted, LeadStatus.converted]
    approved = await count(Reply, Reply.status.in_([ReplyStatus.approved, ReplyStatus.sent, ReplyStatus.failed]))
    rejected = await count(Reply, Reply.status == ReplyStatus.rejected)
    reviewed = approved + rejected

    return AnalyticsOut(
        leads_total=await count(Lead),
        leads_qualified=await count(Lead, Lead.status.in_(qualified_states)),
        replies_pending=await count(Reply, Reply.status == ReplyStatus.pending_review),
        replies_sent=await count(Reply, Reply.status == ReplyStatus.sent),
        approval_rate=round(approved / reviewed, 3) if reviewed else None,
    )
