from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 - register models on Base.metadata


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().db_auto_create:
        # Dev convenience only; use Alembic migrations in production.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Reddit AI Outreach Platform", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)


@app.get("/api/health")
async def health():
    settings = get_settings()
    return {"status": "ok", "reddit_mode": settings.reddit_mode, "llm_mode": settings.llm_mode}
