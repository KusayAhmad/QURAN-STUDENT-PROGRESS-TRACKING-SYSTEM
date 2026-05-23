"""Class schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    academic_year: str = Field(min_length=1, max_length=16)
    teacher_id: UUID | None = None


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    academic_year: str | None = Field(default=None, min_length=1, max_length=16)
    teacher_id: UUID | None = None


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    teacher_id: UUID | None
    name: str
    academic_year: str
    created_at: datetime
    updated_at: datetime
