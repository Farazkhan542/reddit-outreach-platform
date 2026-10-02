import asyncio
import logging
import uuid
from datetime import datetime, timezone

from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import TenantConfig
from app.services.pipeline import run_pipeline_for_org
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()
redis = Redis.from_url(settings.redis_url)


def _run(coro_fn, *args):
    """Run an async DB job from a sync Celery task with a fresh, loop-local engine."""

    async def runner():
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                return await coro_fn(db, *args)
        finally:
            await engine.dispose()

    return asyncio.run(runner())


@celery_app.task
def dispatch_tenant_polls() -> int:
    """Enqueue a poll for every live tenant whose interval has elapsed."""

    async def due_orgs(db):
        configs = (await db.scalars(select(TenantConfig).where(TenantConfig.is_live.is_(True)))).all()
        now = datetime.now(timezone.utc).timestamp()
        due = []
        for c in configs:
            last = float(redis.get(f"last_poll:{c.org_id}") or 0)
            if now - last >= c.poll_interval_minutes * 60:
                due.append(str(c.org_id))
        return due

    orgs = _run(due_orgs)
    for org_id in orgs:
        redis.set(f"last_poll:{org_id}", datetime.now(timezone.utc).timestamp())
        poll_tenant.delay(org_id)
    return len(orgs)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_tenant(self, org_id: str) -> dict:
    try:
        result = _run(run_pipeline_for_org, uuid.UUID(org_id))
        return result.model_dump()
    except Exception as exc:
        logger.exception("pipeline failed for org %s", org_id)
        raise self.retry(exc=exc)
