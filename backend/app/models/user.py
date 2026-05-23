"""User model with role-based access."""
import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.school import School


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.TEACHER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    school_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    school: Mapped["School | None"] = relationship(back_populates="users", lazy="joined")
