"""Observation schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.observation import ObservationType


class ObservationCreate(BaseModel):
    type: ObservationType = ObservationType.GENERAL
    message: str = Field(min_length=1, max_length=4000)


class ObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    teacher_id: UUID | None
    type: ObservationType
    message: str
    created_at: datetime
    updated_at: datetime
