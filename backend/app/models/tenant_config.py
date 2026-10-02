import uuid

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import ApprovalMode, DistributionStrategy


class TenantConfig(IdMixin, TimestampMixin, Base):
    """Per-organization niche configuration, passed as context into every agent run."""

    __tablename__ = "tenant_configs"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), unique=True)
    niche: Mapped[str] = mapped_column(String(200), default="")
    product_description: Mapped[str] = mapped_column(Text, default="")
    subreddits: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    personas: Mapped[list[str]] = mapped_column(JSON, default=list)
    tone: Mapped[str] = mapped_column(String(100), default="friendly, helpful, not salesy")
    approval_mode: Mapped[ApprovalMode] = mapped_column(
        Enum(ApprovalMode, native_enum=False), default=ApprovalMode.manual
    )
    distribution_strategy: Mapped[DistributionStrategy] = mapped_column(
        Enum(DistributionStrategy, native_enum=False), default=DistributionStrategy.round_robin
    )
    intent_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_live: Mapped[bool] = mapped_column(default=False)

    organization: Mapped["Organization"] = relationship(back_populates="tenant_config")  # noqa: F821
