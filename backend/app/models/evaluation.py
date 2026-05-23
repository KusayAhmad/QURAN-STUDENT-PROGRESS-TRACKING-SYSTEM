"""Evaluation model: tracks exams / oral recitation sessions."""
import enum
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class EvaluationType(str, enum.Enum):
    """Categories of evaluation a teacher can record."""

    ORAL_RECITATION = "ORAL_RECITATION"
    REVISION_EXAM = "REVISION_EXAM"
    MONTHLY_REVIEW = "MONTHLY_REVIEW"
    ACCURACY_TEST = "ACCURACY_TEST"
    OTHER = "OTHER"


def _score_check(name: str) -> CheckConstraint:
    return CheckConstraint(
        f"{name} IS NULL OR ({name} >= 0 AND {name} <= 100)",
        name=f"{name}_range",
    )


class Evaluation(UUIDPKMixin, TimestampMixin, Base):
    """A graded evaluation session per the blueprint Module E.

    All score fields are 0-100 and nullable so partial recording is fine.
    """

    __tablename__ = "evaluations"
    __table_args__ = (
        _score_check("tajweed_score"),
        _score_check("accuracy_score"),
        _score_check("fluency_score"),
        _score_check("retention_score"),
        _score_check("speed_score"),
        _score_check("confidence_score"),
        _score_check("overall_score"),
    )

    student_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[EvaluationType] = mapped_column(
        Enum(EvaluationType, name="evaluation_type"), nullable=False
    )
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)

    tajweed_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fluency_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship()
    teacher: Mapped["User | None"] = relationship(foreign_keys=[teacher_id])
