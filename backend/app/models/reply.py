import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import ReplyStatus


class Reply(IdMixin, TimestampMixin, Base):
    """An agent-drafted reply. The app never posts it: a person approves it, posts it
    themselves on reddit.com, then marks it as posted."""

    __tablename__ = "replies"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id"), index=True)
    draft_body: Mapped[str] = mapped_column(Text)
    final_body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReplyStatus] = mapped_column(
        Enum(ReplyStatus, native_enum=False), default=ReplyStatus.pending_review
    )

    # Audit trail: who approved it, and who posted it manually and where.
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posted_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posted_url: Mapped[str | None] = mapped_column(String(500))
