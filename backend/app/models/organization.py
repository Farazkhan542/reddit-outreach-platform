from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200))

    users: Mapped[list["User"]] = relationship(back_populates="organization")  # noqa: F821
    tenant_config: Mapped["TenantConfig | None"] = relationship(  # noqa: F821
        back_populates="organization", uselist=False
    )
