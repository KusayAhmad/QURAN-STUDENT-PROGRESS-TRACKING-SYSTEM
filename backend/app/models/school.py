"""School (tenant) model."""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.student import Student
    from app.models.user import User


class School(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    users: Mapped[list["User"]] = relationship(back_populates="school")
    classes: Mapped[list["Class"]] = relationship(back_populates="school")
    students: Mapped[list["Student"]] = relationship(back_populates="school")
