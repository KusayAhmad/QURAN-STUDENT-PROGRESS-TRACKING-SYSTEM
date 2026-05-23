"""Student schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.student import StudentGender, StudentStatus


class StudentBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    gender: StudentGender
    birth_date: date | None = None
    enrollment_date: date | None = None
    guardian_name: str | None = Field(default=None, max_length=200)
    guardian_phone: str | None = Field(default=None, max_length=40)
    notes: str | None = None
    class_id: UUID | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    gender: StudentGender | None = None
    birth_date: date | None = None
    enrollment_date: date | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    notes: str | None = None
    class_id: UUID | None = None
    status: StudentStatus | None = None


class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    status: StudentStatus
    created_at: datetime
    updated_at: datetime
