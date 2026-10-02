import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.models.enums import Role


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), default=Role.member)
    is_active: Mapped[bool] = mapped_column(default=True)

    organization: Mapped["Organization"] = relationship(back_populates="users")  # noqa: F821
    reddit_account: Mapped["RedditAccount | None"] = relationship(  # noqa: F821
        back_populates="user", uselist=False
    )
