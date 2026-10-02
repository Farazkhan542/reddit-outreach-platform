from fastapi import APIRouter

from app.api.v1 import approval, auth, config, leads, org, pipeline, replies

api_router = APIRouter(prefix="/api/v1")
for module in (auth, org, config, leads, replies, pipeline, approval):
    api_router.include_router(module.router)
