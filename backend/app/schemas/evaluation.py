"""Evaluation schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluation import EvaluationType


class EvaluationCreate(BaseModel):
    type: EvaluationType
    exam_date: date
    tajweed_score: int | None = Field(default=None, ge=0, le=100)
    accuracy_score: int | None = Field(default=None, ge=0, le=100)
    fluency_score: int | None = Field(default=None, ge=0, le=100)
    retention_score: int | None = Field(default=None, ge=0, le=100)
    speed_score: int | None = Field(default=None, ge=0, le=100)
    confidence_score: int | None = Field(default=None, ge=0, le=100)
    overall_score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class EvaluationUpdate(BaseModel):
    """Partial update — every field optional. Score recomputation is NOT
    performed on update; if you want overall to track new axes, send it
    explicitly."""

    type: EvaluationType | None = None
    exam_date: date | None = None
    tajweed_score: int | None = Field(default=None, ge=0, le=100)
    accuracy_score: int | None = Field(default=None, ge=0, le=100)
    fluency_score: int | None = Field(default=None, ge=0, le=100)
    retention_score: int | None = Field(default=None, ge=0, le=100)
    speed_score: int | None = Field(default=None, ge=0, le=100)
    confidence_score: int | None = Field(default=None, ge=0, le=100)
    overall_score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    teacher_id: UUID | None
    type: EvaluationType
    exam_date: date
    tajweed_score: int | None
    accuracy_score: int | None
    fluency_score: int | None
    retention_score: int | None
    speed_score: int | None
    confidence_score: int | None
    overall_score: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
