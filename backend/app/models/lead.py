import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import LeadStatus


class Lead(IdMixin, TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("org_id", "reddit_fullname"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    reddit_fullname: Mapped[str] = mapped_column(String(32))  # e.g. t3_abc123
    subreddit: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(String(400))
    body: Mapped[str] = mapped_column(Text, default="")
    permalink: Mapped[str] = mapped_column(String(500))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    intent_score: Mapped[float | None] = mapped_column(Float)
    intent_reasoning: Mapped[str | None] = mapped_column(Text)
    extracted_needs: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, native_enum=False), default=LeadStatus.new
    )
