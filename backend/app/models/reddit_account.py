import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class RedditAccount(IdMixin, TimestampMixin, Base):
    """A team member's connected Reddit account (read-only scopes). Tokens are Fernet-encrypted at rest."""

    __tablename__ = "reddit_accounts"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    reddit_username: Mapped[str] = mapped_column(String(100))
    access_token_enc: Mapped[str | None] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str] = mapped_column(String(200), default="identity read")

    # Account health
    karma: Mapped[int] = mapped_column(Integer, default=0)
    removal_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped["User"] = relationship(back_populates="reddit_account")  # noqa: F821
