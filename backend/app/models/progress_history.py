"""ProgressHistory: append-only timeline of memorization_progress changes.

One row per write to memorization_progress (CREATE or UPDATE). The current
state lives in `memorization_progress`; everything older lives here.

This is what enables the per-surah mastery timeline
(blueprint §12-A: 'Baqarah: Weak -> Review -> Strong -> Mastered').
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.audit_log import AuditAction
from app.models.memorization_progress import MemorizationStatus
from app.models.mixins import GUID, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class ProgressHistory(UUIDPKMixin, Base):
    __tablename__ = "progress_history"

    progress_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("memorization_progress.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[UUID] = mapped_column(GUID(), nullable=False, index=True)
    surah_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    teacher_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Snapshot of memorization_progress at the time of write.
    status: Mapped[MemorizationStatus] = mapped_column(
        Enum(MemorizationStatus, name="memorization_status"), nullable=False
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Was this row written as a CREATE or UPDATE on memorization_progress?
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    teacher: Mapped["User | None"] = relationship(foreign_keys=[teacher_id])
