"""Notification schemas (read-only — notifications are produced server-side)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user_id: UUID
    school_id: UUID | None
    type: NotificationType
    title: str
    message: str
    payload: dict | None
    read_at: datetime | None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    unread: int
