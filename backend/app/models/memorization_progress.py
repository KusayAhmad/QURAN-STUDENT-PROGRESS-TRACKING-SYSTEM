"""Memorization progress: the core (student, surah) status table."""
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.surah import QuranSurah
    from app.models.user import User


class MemorizationStatus(str, enum.Enum):
    """Normalized states replacing Excel cell colors."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    WEAK = "WEAK"
    STRONG = "STRONG"
    MASTERED = "MASTERED"


class MemorizationProgress(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "memorization_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "surah_id", name="uq_memorization_progress_student_surah"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="score_range"),
        CheckConstraint(
            "completion_percent >= 0 AND completion_percent <= 100",
            name="completion_percent_range",
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    surah_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quran_surahs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    teacher_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[MemorizationStatus] = mapped_column(
        Enum(MemorizationStatus, name="memorization_status"),
        nullable=False,
        default=MemorizationStatus.NOT_STARTED,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="progress")
    surah: Mapped["QuranSurah"] = relationship(lazy="joined")
    teacher: Mapped["User | None"] = relationship(foreign_keys=[teacher_id])
