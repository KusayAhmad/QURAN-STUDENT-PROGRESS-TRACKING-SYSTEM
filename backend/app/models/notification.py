"""Notification model — per-user inbox.

For MVP, notifications are in-app only. Email/push channels are a future
slice; the schema is designed so adding a `channel` enum + delivery_status
field later doesn't require a migration of existing data.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.user import User


class NotificationType(str, enum.Enum):
    """Why this notification was raised. Drives UI iconography + filtering."""

    PROGRESS_REGRESSED = "PROGRESS_REGRESSED"
    LOW_EVALUATION = "LOW_EVALUATION"
    STUDENT_ADDED = "STUDENT_ADDED"
    OVERDUE_REVIEW = "OVERDUE_REVIEW"  # reserved for the scheduled-scan slice
    MANUAL = "MANUAL"  # admin-test or future manual broadcasts


class Notification(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    recipient_user_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_id: Mapped[UUID | None] = mapped_column(
        GUID(),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Free-form payload for the frontend to deep-link, e.g. {"student_id": "..."}
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_user_id])
    school: Mapped["School | None"] = relationship(foreign_keys=[school_id])
