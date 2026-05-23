"""Student model."""
import enum
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.memorization_progress import MemorizationProgress
    from app.models.school import School


class StudentGender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    GRADUATED = "GRADUATED"


class Student(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "students"

    school_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    gender: Mapped[StudentGender] = mapped_column(Enum(StudentGender, name="student_gender"))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    enrollment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, name="student_status"), nullable=False, default=StudentStatus.ACTIVE
    )

    school: Mapped["School"] = relationship(back_populates="students")
    class_: Mapped["Class | None"] = relationship(back_populates="students")
    progress: Mapped[list["MemorizationProgress"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
