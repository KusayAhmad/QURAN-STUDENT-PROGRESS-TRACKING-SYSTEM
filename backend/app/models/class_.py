"""Class (group of students taught by a teacher) model."""
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.student import Student
    from app.models.user import User


class Class(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "classes"

    school_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(16), nullable=False)

    school: Mapped["School"] = relationship(back_populates="classes")
    teacher: Mapped["User | None"] = relationship(foreign_keys=[teacher_id])
    students: Mapped[list["Student"]] = relationship(back_populates="class_")
