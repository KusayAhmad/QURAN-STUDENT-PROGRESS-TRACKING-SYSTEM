"""ProgressHistory schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditAction
from app.models.memorization_progress import MemorizationStatus


class ProgressHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    progress_id: UUID
    student_id: UUID
    surah_id: int
    teacher_id: UUID | None
    status: MemorizationStatus
    score: int | None
    completion_percent: int
    notes: str | None
    action: AuditAction
    recorded_at: datetime
