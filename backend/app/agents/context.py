import uuid

from pydantic import BaseModel

from app.models import TenantConfig


class TenantContext(BaseModel):
    """Typed context passed into every agent run, so one agent codebase serves every niche."""

    org_id: uuid.UUID
    niche: str
    product_description: str
    subreddits: list[str]
    keywords: list[str]
    personas: list[str]
    tone: str
    intent_threshold: float

    @classmethod
    def from_config(cls, config: TenantConfig) -> "TenantContext":
        return cls(
            org_id=config.org_id,
            niche=config.niche,
            product_description=config.product_description,
            subreddits=list(config.subreddits or []),
            keywords=list(config.keywords or []),
            personas=list(config.personas or []),
            tone=config.tone,
            intent_threshold=config.intent_threshold,
        )