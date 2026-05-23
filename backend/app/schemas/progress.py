"""Memorization progress schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.memorization_progress import MemorizationStatus


class ProgressUpsert(BaseModel):
    """Used by POST (upsert by student_id+surah_id) and PUT."""

    surah_id: int
    status: MemorizationStatus
    score: int | None = Field(default=None, ge=0, le=100)
    completion_percent: int = Field(default=0, ge=0, le=100)
    notes: str | None = None
    last_reviewed_at: datetime | None = None


class ProgressUpdate(BaseModel):
    """Partial update — surah_id is taken from the URL, not the body."""

    status: MemorizationStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    completion_percent: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    last_reviewed_at: datetime | None = None


class ProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    surah_id: int
    teacher_id: UUID | None
    status: MemorizationStatus
    score: int | None
    completion_percent: int
    last_reviewed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
