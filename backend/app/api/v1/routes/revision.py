"""Revision-suggestion routes (blueprint §12-C: Smart Revision Suggestions)."""
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DbSession, SchoolUser
from app.schemas.revision import RevisionSuggestionList
from app.services import revision_service
from app.services.revision_service import DEFAULT_LIMIT, MAX_LIMIT

router = APIRouter(tags=["revision"])


@router.get(
    "/students/{student_id}/revision-suggestions",
    response_model=RevisionSuggestionList,
)
async def revision_suggestions(
    student_id: UUID,
    db: DbSession,
    user: SchoolUser,
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> RevisionSuggestionList:
    """Return up to ``limit`` ranked revision suggestions.

    Each suggestion carries a ``reason`` enum (WEAK, REVIEW_REQUIRED,
    STALE_MASTERED, STALE_STRONG, IN_PROGRESS) and a ``priority_score`` for
    ordering. The list is already sorted, so the client can render it as-is.
    """
    return await revision_service.suggest_revisions(
        db,
        school_id=user.school_id,
        student_id=student_id,
        limit=limit,
    )
