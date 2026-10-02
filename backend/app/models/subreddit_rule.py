import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class SubredditRule(IdMixin, TimestampMixin, Base):
    """Per-org record of a subreddit's self-promotion policy, checked before drafting."""

    __tablename__ = "subreddit_rules"
    __table_args__ = (UniqueConstraint("org_id", "subreddit"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    subreddit: Mapped[str] = mapped_column(String(100))
    allows_commercial_replies: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text)
