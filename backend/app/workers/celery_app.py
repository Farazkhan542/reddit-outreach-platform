from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("outreach", broker=settings.redis_url, backend=settings.redis_url, include=["app.workers.tasks"])
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    beat_schedule={
        # Ticks every minute; each tenant is polled on its own `poll_interval_minutes`.
        "dispatch-tenant-polls": {"task": "app.workers.tasks.dispatch_tenant_polls", "schedule": 60.0},
    },
)
