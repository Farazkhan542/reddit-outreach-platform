import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class PostingMode(str, enum.Enum):
    # manual: members copy approved replies and post them themselves -> read-only API scopes.
    manual = "manual"
    api = "api"


class ApplicationStatus(str, enum.Enum):
    not_started = "not_started"
    submitted = "submitted"
    approved = "approved"
    denied = "denied"


class ApiAccessApplication(IdMixin, TimestampMixin, Base):
    """Tracks an org's Reddit Data API access request (Responsible Builder Policy)."""

    __tablename__ = "api_access_applications"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), unique=True)
    app_name: Mapped[str] = mapped_column(String(100), default="")
    company_name: Mapped[str] = mapped_column(String(200), default="")
    website_url: Mapped[str] = mapped_column(String(500), default="")
    privacy_policy_url: Mapped[str] = mapped_column(String(500), default="")
    contact_email: Mapped[str] = mapped_column(String(320), default="")
    reddit_username: Mapped[str] = mapped_column(String(100), default="")
    reddit_account_age_days: Mapped[int] = mapped_column(Integer, default=0)
    posting_mode: Mapped[PostingMode] = mapped_column(
        Enum(PostingMode, native_enum=False), default=PostingMode.manual
    )
    # False = free non-commercial tier (internal development/testing only).
    is_commercial: Mapped[bool] = mapped_column(default=False)
    data_retention_days: Mapped[int] = mapped_column(Integer, default=90)

    steps_done: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False), default=ApplicationStatus.not_started
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
