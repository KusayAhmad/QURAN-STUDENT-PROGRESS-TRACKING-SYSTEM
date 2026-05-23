"""Analytics response schemas (Module F)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.memorization_progress import MemorizationStatus


class StatusCounts(BaseModel):
    """Histogram of progress rows by status. Surahs with no row are NOT_STARTED."""

    NOT_STARTED: int = 0
    IN_PROGRESS: int = 0
    REVIEW_REQUIRED: int = 0
    WEAK: int = 0
    STRONG: int = 0
    MASTERED: int = 0


class StudentAnalytics(BaseModel):
    """Per-student stats. The Excel-replacement KPI surface."""

    student_id: UUID
    full_name: str

    total_surahs: int
    counts_by_status: StatusCounts

    # Two complementary views of "completion":
    #   mastery_percent     = MASTERED / total_surahs       (strict)
    #   avg_completion_pct  = mean of completion_percent across recorded surahs
    mastery_percent: float
    avg_completion_pct: float

    mastered_surah_ids: list[int]
    weak_surah_ids: list[int]
    review_required_surah_ids: list[int]

    last_activity_at: datetime | None
    recent_evaluations_avg_score: float | None
    recent_evaluations_count: int


class ClassAnalytics(BaseModel):
    class_id: UUID
    class_name: str
    student_count: int
    avg_mastery_percent: float
    avg_completion_pct: float
    counts_by_status: StatusCounts


class SchoolAnalytics(BaseModel):
    school_id: UUID
    student_count: int
    avg_mastery_percent: float
    avg_completion_pct: float
    counts_by_status: StatusCounts


__all__ = [
    "ClassAnalytics",
    "MemorizationStatus",
    "SchoolAnalytics",
    "StatusCounts",
    "StudentAnalytics",
]
