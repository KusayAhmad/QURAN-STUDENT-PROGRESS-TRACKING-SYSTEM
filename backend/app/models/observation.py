"""Observation model: teacher notes about a student (Module G)."""
import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class ObservationType(str, enum.Enum):
    DAILY_NOTE = "DAILY_NOTE"
    WEAK_PRONUNCIATION = "WEAK_PRONUNCIATION"
    MISSING_REVISION = "MISSING_REVISION"
    IMPROVEMENT = "IMPROVEMENT"
    PARENT_DISCUSSION = "PARENT_DISCUSSION"
    GENERAL = "GENERAL"


class Observation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "observations"

    student_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[ObservationType] = mapped_column(
        Enum(ObservationType, name="observation_type"),
        nullable=False,
        default=ObservationType.GENERAL,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)

    student: Mapped["Student"] = relationship()
    teacher: Mapped["User | None"] = relationship(foreign_keys=[teacher_id])
