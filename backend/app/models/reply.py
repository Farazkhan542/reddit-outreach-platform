import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import ReplyKind, ReplyStatus


class Reply(IdMixin, TimestampMixin, Base):
    """An agent-drafted reply. Nothing is sent until a human approves it."""

    __tablename__ = "replies"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id"), index=True)
    kind: Mapped[ReplyKind] = mapped_column(
        Enum(ReplyKind, native_enum=False), default=ReplyKind.comment
    )
    draft_body: Mapped[str] = mapped_column(Text)
    final_body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReplyStatus] = mapped_column(
        Enum(ReplyStatus, native_enum=False), default=ReplyStatus.pending_review
    )

    # Audit trail: who approved it and which account sent it.
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_from_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("reddit_accounts.id"))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reddit_thing_id: Mapped[str | None] = mapped_column(String(32))
    error: Mapped[str | None] = mapped_column(Text)
