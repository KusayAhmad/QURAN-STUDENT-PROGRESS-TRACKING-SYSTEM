"""Revision-suggestion schemas (Module §12-C: Smart Revision Suggestions).

The recommender is rule-based — no ML model — so each suggestion carries a
human-readable ``reason`` enum that the UI can localize, plus a numeric
``priority_score`` so the frontend can render a "top N" list without re-sorting.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.models.memorization_progress import MemorizationStatus


class RevisionReason(str, Enum):
    """Why a particular surah was suggested for revision.

    Ordered roughly by urgency (most urgent first). The service emits the
    *single* most-relevant reason per surah; we don't want a noisy list.
    """

    WEAK = "WEAK"  # status == WEAK
    REVIEW_REQUIRED = "REVIEW_REQUIRED"  # status == REVIEW_REQUIRED
    STALE_MASTERED = "STALE_MASTERED"  # MASTERED but not touched in > N days
    STALE_STRONG = "STALE_STRONG"  # STRONG but not touched in > N days
    IN_PROGRESS = "IN_PROGRESS"  # actively learning — keep momentum


class RevisionSuggestion(BaseModel):
    """One row in the suggested-revision list."""

    surah_id: int
    surah_name_en: str
    surah_name_ar: str
    current_status: MemorizationStatus
    completion_percent: int
    last_reviewed_at: datetime | None
    days_since_review: int | None
    reason: RevisionReason
    # Higher = more urgent. Pure ordering signal; not exposed as a percentage.
    priority_score: float


class RevisionSuggestionList(BaseModel):
    """Top-N suggestions for a single student."""

    student_id: UUID
    generated_at: datetime
    suggestions: list[RevisionSuggestion]


__all__ = [
    "RevisionReason",
    "RevisionSuggestion",
    "RevisionSuggestionList",
]
