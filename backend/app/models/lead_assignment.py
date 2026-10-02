import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class LeadAssignment(IdMixin, TimestampMixin, Base):
    __tablename__ = "lead_assignments"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id"), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    reddit_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("reddit_accounts.id"))
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
