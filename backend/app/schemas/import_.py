"""Schemas for the legacy-Excel import endpoint."""
from pydantic import BaseModel


class ImportError(BaseModel):
    sheet: str
    row: int
    message: str


class ImportResult(BaseModel):
    students_created: int = 0
    students_matched: int = 0
    progress_recorded: int = 0
    errors: list[ImportError] = []
