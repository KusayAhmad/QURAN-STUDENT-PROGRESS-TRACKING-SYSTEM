"""Smart revision suggestions (blueprint §12-C).

A rule-based recommender: no ML, no training data, no infra. The blueprint
example output is

    Student should revise:
      Al-Mulk
      Al-Kahf
      Ya-Sin

We turn that into a typed list ranked by urgency. The two signals are:

1. **Status** — WEAK and REVIEW_REQUIRED surahs are the most urgent.
   IN_PROGRESS surahs are kept on the list to maintain momentum.
2. **Staleness** — MASTERED and STRONG surahs decay if they aren't refreshed.
   We surface them once they cross a threshold so memorization quality holds.

Rationale for going rule-based:
- Volume is small (~hundreds of progress rows per student) — no need for a
  scoring model.
- Reasons must be explainable to teachers (the UI shows *why* each surah
  was picked). A rule per reason is easy to localize and audit.
- We can swap the scorer for a learned model later without changing the
  router or schema (this service is the single replacement point).

Tunables (top of file) are deliberately module-level so they're easy to
sweep in tests or future config without threading args through the API.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memorization_progress import MemorizationProgress, MemorizationStatus
from app.models.surah import QuranSurah
from app.repositories import student_repo
from app.schemas.revision import (
    RevisionReason,
    RevisionSuggestion,
    RevisionSuggestionList,
)

# Days after which MASTERED / STRONG surahs are considered stale and worth
# revisiting. Memorization decay is non-linear; these are conservative defaults
# matching what most huffaz teachers use as a rolling-revision cadence.
STALE_MASTERED_DAYS = 30
STALE_STRONG_DAYS = 14

# Base scores per reason. Higher = more urgent. The exact magnitudes don't
# matter — only the ordering does — but we leave headroom (gaps of 10) so
# completion-percent and recency tweaks can break ties without crossing tiers.
_BASE_SCORE = {
    RevisionReason.WEAK: 100.0,
    RevisionReason.REVIEW_REQUIRED: 80.0,
    RevisionReason.STALE_STRONG: 60.0,
    RevisionReason.STALE_MASTERED: 50.0,
    RevisionReason.IN_PROGRESS: 40.0,
}

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


def _days_since(dt: datetime | None, now: datetime) -> int | None:
    """Robust diff that handles naive timestamps (SQLite returns naive datetimes)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max((now - dt).days, 0)


def _classify(
    progress: MemorizationProgress, now: datetime
) -> tuple[RevisionReason, float] | None:
    """Decide whether this progress row should be suggested, and at what score.

    Returns None when the row should be skipped (e.g. NOT_STARTED is not a
    revision candidate — the student hasn't begun). Tie-breakers (completion
    percent, days since review) are folded into the score so the caller can
    sort on a single number.
    """
    days = _days_since(progress.last_reviewed_at, now)

    if progress.status == MemorizationStatus.WEAK:
        # Weak is *always* highest priority. Lower completion = even higher
        # urgency (subtract from 100 so 0%-complete weak surahs beat 90%-complete).
        score = _BASE_SCORE[RevisionReason.WEAK] + (100 - progress.completion_percent) * 0.1
        return RevisionReason.WEAK, score

    if progress.status == MemorizationStatus.REVIEW_REQUIRED:
        score = _BASE_SCORE[RevisionReason.REVIEW_REQUIRED]
        if days is not None:
            score += min(days, 30) * 0.5  # the longer it's been, the more urgent
        return RevisionReason.REVIEW_REQUIRED, score

    if progress.status == MemorizationStatus.IN_PROGRESS:
        # Keep momentum on actively-learned surahs, but only if the student
        # has actually been working on them (>10% complete) — a 0%-complete
        # IN_PROGRESS row is just noise.
        if progress.completion_percent < 10:
            return None
        score = _BASE_SCORE[RevisionReason.IN_PROGRESS] + progress.completion_percent * 0.05
        return RevisionReason.IN_PROGRESS, score

    if progress.status == MemorizationStatus.STRONG:
        if days is None or days < STALE_STRONG_DAYS:
            return None
        # Older = more urgent, capped so a 6-month-old STRONG doesn't outrank
        # a fresh WEAK.
        score = _BASE_SCORE[RevisionReason.STALE_STRONG] + min(days, 60) * 0.1
        return RevisionReason.STALE_STRONG, score

    if progress.status == MemorizationStatus.MASTERED:
        if days is None or days < STALE_MASTERED_DAYS:
            return None
        score = _BASE_SCORE[RevisionReason.STALE_MASTERED] + min(days, 90) * 0.05
        return RevisionReason.STALE_MASTERED, score

    # NOT_STARTED, anything unknown -> not a revision candidate
    return None


async def suggest_revisions(
    db: AsyncSession,
    *,
    school_id: UUID,
    student_id: UUID,
    limit: int = DEFAULT_LIMIT,
) -> RevisionSuggestionList:
    """Return up to ``limit`` ranked revision suggestions for the student.

    The query is one round-trip: we join progress to surahs to get the
    bilingual names in the same row. Ranking is done in Python because the
    rule logic is non-trivial and SQLite doesn't have CASE expressions
    flexible enough for the staleness windows without dialect-specific SQL.
    Volumes are tiny (≤114 rows per student), so this is fine.
    """
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"limit must be between 1 and {MAX_LIMIT}",
        )

    # Tenant + existence check via the standard helper.
    student = await student_repo.get_for_school(
        db, school_id=school_id, student_id=student_id
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    rows = (
        await db.execute(
            select(MemorizationProgress, QuranSurah)
            .join(QuranSurah, QuranSurah.id == MemorizationProgress.surah_id)
            .where(MemorizationProgress.student_id == student_id)
        )
    ).all()

    now = datetime.now(timezone.utc)
    candidates: list[RevisionSuggestion] = []
    for progress, surah in rows:
        classified = _classify(progress, now)
        if classified is None:
            continue
        reason, score = classified
        candidates.append(
            RevisionSuggestion(
                surah_id=surah.id,
                surah_name_en=surah.surah_name_en,
                surah_name_ar=surah.surah_name_ar,
                current_status=progress.status,
                completion_percent=progress.completion_percent,
                last_reviewed_at=progress.last_reviewed_at,
                days_since_review=_days_since(progress.last_reviewed_at, now),
                reason=reason,
                priority_score=round(score, 2),
            )
        )

    # Sort by score desc, then surah_id asc as a stable tiebreaker (mostly so
    # tests don't depend on dict insertion order).
    candidates.sort(key=lambda s: (-s.priority_score, s.surah_id))
    top = candidates[:limit]

    return RevisionSuggestionList(
        student_id=student_id,
        generated_at=now,
        suggestions=top,
    )
