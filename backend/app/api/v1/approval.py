from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DB, Admin
from app.models import (
    ApiAccessApplication,
    ApplicationStatus,
    SubredditRule,
    TenantConfig,
)
from app.schemas import ORM
from app.services.approval import STEP_IDS, STEPS, CheckResult, GuideStep, build_request_text, run_checks

router = APIRouter(prefix="/approval", tags=["approval"])


class ApplicationIn(BaseModel):
    app_name: str = ""
    company_name: str = ""
    website_url: str = ""
    privacy_policy_url: str = ""
    contact_email: str = ""
    reddit_username: str = ""
    reddit_account_age_days: int = Field(0, ge=0)
    is_commercial: bool = False
    data_retention_days: int = Field(90, ge=0)
    steps_done: list[str] = []
    status: ApplicationStatus = ApplicationStatus.not_started
    reviewer_notes: str | None = None


class ApplicationOut(ApplicationIn, ORM):
    submitted_at: datetime | None


class GuideOut(BaseModel):
    application: ApplicationOut
    steps: list[GuideStep]
    check: CheckResult
    request_text: str


async def _load(db, org_id):
    app = await db.scalar(select(ApiAccessApplication).where(ApiAccessApplication.org_id == org_id))
    if app is None:
        app = ApiAccessApplication(org_id=org_id)
        db.add(app)
        await db.flush()
    config = await db.scalar(select(TenantConfig).where(TenantConfig.org_id == org_id))
    if config is None:
        config = TenantConfig(org_id=org_id)
        db.add(config)
        await db.flush()
    rules = (await db.scalars(select(SubredditRule).where(SubredditRule.org_id == org_id))).all()
    return app, config, list(rules)


def _guide(app, config, rules) -> GuideOut:
    return GuideOut(
        application=ApplicationOut.model_validate(app),
        steps=STEPS,
        check=run_checks(app, config, rules),
        request_text=build_request_text(app, config),
    )


@router.get("", response_model=GuideOut)
async def get_guide(current: Admin, db: DB):
    """Everything the approval page needs: saved answers, steps, a fresh readiness check, request draft."""
    app, config, rules = await _load(db, current.org_id)
    await db.commit()
    return _guide(app, config, rules)


@router.put("", response_model=GuideOut)
async def save_application(data: ApplicationIn, current: Admin, db: DB):
    app, config, rules = await _load(db, current.org_id)
    values = data.model_dump()
    values["steps_done"] = [s for s in values["steps_done"] if s in STEP_IDS]
    if values["status"] == ApplicationStatus.submitted and app.submitted_at is None:
        app.submitted_at = datetime.now(timezone.utc)
    for field, value in values.items():
        setattr(app, field, value)
    await db.commit()
    return _guide(app, config, rules)


@router.post("/check", response_model=CheckResult)
async def check_now(current: Admin, db: DB):
    app, config, rules = await _load(db, current.org_id)
    await db.commit()
    return run_checks(app, config, rules)
