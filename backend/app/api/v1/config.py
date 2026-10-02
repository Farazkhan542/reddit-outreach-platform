import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.agents import NicheInterpreterAgent
from app.agents.schemas import NicheConfigSuggestion
from app.api.deps import DB, Admin
from app.models import SubredditRule, TenantConfig
from app.schemas import (
    InterpretIn,
    SubredditRuleIn,
    SubredditRuleOut,
    TenantConfigBase,
    TenantConfigOut,
)

router = APIRouter(prefix="/config", tags=["config"])


async def _get_config(db, org_id) -> TenantConfig:
    config = await db.scalar(select(TenantConfig).where(TenantConfig.org_id == org_id))
    if config is None:
        config = TenantConfig(org_id=org_id)
        db.add(config)
        await db.flush()
    return config


@router.get("", response_model=TenantConfigOut)
async def get_config(current: Admin, db: DB):
    config = await _get_config(db, current.org_id)
    await db.commit()
    return config


@router.put("", response_model=TenantConfigOut)
async def update_config(data: TenantConfigBase, current: Admin, db: DB):
    config = await _get_config(db, current.org_id)
    for field, value in data.model_dump().items():
        setattr(config, field, value)
    await db.commit()
    return config


@router.post("/interpret", response_model=NicheConfigSuggestion)
async def interpret_niche(data: InterpretIn, current: Admin):
    """Suggests a starter config from a plain-language description. Nothing is saved."""
    return await NicheInterpreterAgent().run(data.description)


@router.get("/subreddit-rules", response_model=list[SubredditRuleOut])
async def list_rules(current: Admin, db: DB):
    return (await db.scalars(select(SubredditRule).where(SubredditRule.org_id == current.org_id))).all()


@router.put("/subreddit-rules", response_model=SubredditRuleOut)
async def upsert_rule(data: SubredditRuleIn, current: Admin, db: DB):
    name = data.subreddit.lower().removeprefix("r/")
    rule = await db.scalar(
        select(SubredditRule).where(SubredditRule.org_id == current.org_id, SubredditRule.subreddit == name)
    )
    if rule is None:
        rule = SubredditRule(org_id=current.org_id, subreddit=name)
        db.add(rule)
    rule.allows_commercial_replies = data.allows_commercial_replies
    rule.notes = data.notes
    await db.commit()
    return rule


@router.delete("/subreddit-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: uuid.UUID, current: Admin, db: DB):
    rule = await db.scalar(
        select(SubredditRule).where(SubredditRule.id == rule_id, SubredditRule.org_id == current.org_id)
    )
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    await db.delete(rule)
    await db.commit()
