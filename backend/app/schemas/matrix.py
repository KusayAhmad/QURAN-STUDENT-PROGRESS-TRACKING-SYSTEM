"""Bulk matrix schema — the Excel-replacement view.

Returns one big payload (students + their progress + surah catalog) so the
frontend can render the full Quran × Student grid in a single fetch.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.memorization_progress import MemorizationStatus
from app.schemas.surah import SurahRead


class MatrixCell(BaseModel):
    surah_id: int
    status: MemorizationStatus
    completion_percent: int


class MatrixStudent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    class_id: UUID | None
    cells: list[MatrixCell]


class MatrixView(BaseModel):
    surahs: list[SurahRead]
    students: list[MatrixStudent]
