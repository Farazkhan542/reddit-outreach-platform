"""Scout -> Classifier -> Drafter pipeline for one tenant. Output lands in the human review queue."""

import logging
import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import ClassifierAgent, DrafterAgent, ScoutAgent, TenantContext
from app.integrations.reddit import get_reddit_client
from app.models import Lead, LeadStatus, Reply, ReplyStatus, TenantConfig
from app.services.compliance import can_reply
from app.services.distribution import assign_lead

logger = logging.getLogger(__name__)


class PipelineResult(BaseModel):
    scanned: int = 0
    new_leads: int = 0
    qualified: int = 0
    drafts: int = 0
    skipped_by_rules: int = 0


async def run_pipeline_for_org(db: AsyncSession, org_id: uuid.UUID) -> PipelineResult:
    config = await db.scalar(select(TenantConfig).where(TenantConfig.org_id == org_id))
    if config is None:
        raise ValueError(f"org {org_id} has no tenant config")

    ctx = TenantContext.from_config(config)
    scout = ScoutAgent(get_reddit_client())
    classifier = ClassifierAgent()
    drafter = DrafterAgent()
    result = PipelineResult()

    posts = await scout.run(ctx)
    result.scanned = len(posts)

    seen = set(
        (await db.scalars(
            select(Lead.reddit_fullname).where(
                Lead.org_id == org_id, Lead.reddit_fullname.in_([p.fullname for p in posts])
            )
        )).all()
    )

    for post in posts:
        if post.fullname in seen:
            continue

        classification = await classifier.run(ctx, post)
        qualified = classification.intent_score >= ctx.intent_threshold
        lead = Lead(
            id=uuid.uuid4(),
            org_id=org_id,
            reddit_fullname=post.fullname,
            subreddit=post.subreddit,
            author=post.author,
            title=post.title,
            body=post.body,
            permalink=post.permalink,
            posted_at=post.created_at,
            intent_score=classification.intent_score,
            intent_reasoning=classification.reasoning,
            extracted_needs=classification.needs.model_dump(),
            status=LeadStatus.qualified if qualified else LeadStatus.disqualified,
        )
        db.add(lead)
        result.new_leads += 1
        if not qualified:
            continue
        result.qualified += 1

        allowed, reason = await can_reply(db, org_id, post.subreddit)
        if not allowed:
            lead.intent_reasoning = f"{lead.intent_reasoning}\n[compliance] {reason}"
            result.skipped_by_rules += 1
            continue

        draft = await drafter.run(ctx, post, classification)
        db.add(
            Reply(
                org_id=org_id,
                lead_id=lead.id,
                draft_body=draft.body,
                status=ReplyStatus.pending_review,
            )
        )
        result.drafts += 1
        await db.flush()
        await assign_lead(db, lead, config.distribution_strategy)

    await db.commit()
    logger.info("pipeline org=%s result=%s", org_id, result.model_dump())
    return result
