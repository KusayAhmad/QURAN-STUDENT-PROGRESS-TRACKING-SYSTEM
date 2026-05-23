"""Analytics business logic — composes aggregate queries into KPI views."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.memorization_progress import MemorizationStatus
from app.models.student import Student, StudentStatus
from app.repositories import analytics_repo, evaluation_repo, student_repo
from app.schemas.analytics import (
    ClassAnalytics,
    SchoolAnalytics,
    StatusCounts,
    StudentAnalytics,
)

# How many of the most recent evaluations to include in the rolling average.
RECENT_EVAL_WINDOW = 5


def _build_status_counts(
    histogram: dict[MemorizationStatus, int], total_surahs: int
) -> StatusCounts:
    """Implicit NOT_STARTED is total - sum(rows). DB-stored NOT_STARTED rows still count."""
    recorded = sum(histogram.values())
    explicit_not_started = histogram.get(MemorizationStatus.NOT_STARTED, 0)
    implicit_not_started = max(total_surahs - recorded, 0)
    return StatusCounts(
        NOT_STARTED=explicit_not_started + implicit_not_started,
        IN_PROGRESS=histogram.get(MemorizationStatus.IN_PROGRESS, 0),
        REVIEW_REQUIRED=histogram.get(MemorizationStatus.REVIEW_REQUIRED, 0),
        WEAK=histogram.get(MemorizationStatus.WEAK, 0),
        STRONG=histogram.get(MemorizationStatus.STRONG, 0),
        MASTERED=histogram.get(MemorizationStatus.MASTERED, 0),
    )


async def student_analytics(
    db: AsyncSession, *, school_id: UUID, student_id: UUID
) -> StudentAnalytics:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    total_surahs = await analytics_repo.total_surahs(db)
    histogram = await analytics_repo.status_histogram_for_student(db, student_id)
    counts = _build_status_counts(histogram, total_surahs)

    avg_completion = await analytics_repo.avg_completion_for_student(db, student_id)
    mastered_ids = await analytics_repo.surah_ids_by_status(
        db, student_id, MemorizationStatus.MASTERED
    )
    weak_ids = await analytics_repo.surah_ids_by_status(db, student_id, MemorizationStatus.WEAK)
    review_ids = await analytics_repo.surah_ids_by_status(
        db, student_id, MemorizationStatus.REVIEW_REQUIRED
    )

    last_activity = await analytics_repo.last_activity_for_student(db, student_id)
    avg_eval, eval_count = await evaluation_repo.avg_overall_score_for_student(
        db, student_id, last_n=RECENT_EVAL_WINDOW
    )

    mastery_pct = (counts.MASTERED / total_surahs * 100.0) if total_surahs else 0.0

    return StudentAnalytics(
        student_id=student.id,
        full_name=student.full_name,
        total_surahs=total_surahs,
        counts_by_status=counts,
        mastery_percent=round(mastery_pct, 2),
        avg_completion_pct=round(avg_completion, 2),
        mastered_surah_ids=mastered_ids,
        weak_surah_ids=weak_ids,
        review_required_surah_ids=review_ids,
        last_activity_at=last_activity,
        recent_evaluations_avg_score=round(avg_eval, 2) if avg_eval is not None else None,
        recent_evaluations_count=eval_count,
    )


async def class_analytics(
    db: AsyncSession, *, school_id: UUID, class_id: UUID
) -> ClassAnalytics:
    klass = (
        await db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == school_id)
        )
    ).scalar_one_or_none()
    if klass is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")

    total_surahs = await analytics_repo.total_surahs(db)
    histogram = await analytics_repo.status_histogram_for_class(db, class_id)
    per_student = await analytics_repo.per_student_aggregates_for_class(db, class_id)

    student_count = len(per_student)
    if student_count and total_surahs:
        avg_mastery = (
            sum(mc for _, mc, _ in per_student) / student_count / total_surahs * 100.0
        )
        avg_completion = sum(ap for _, _, ap in per_student) / student_count
    else:
        avg_mastery = 0.0
        avg_completion = 0.0

    return ClassAnalytics(
        class_id=klass.id,
        class_name=klass.name,
        student_count=student_count,
        avg_mastery_percent=round(avg_mastery, 2),
        avg_completion_pct=round(avg_completion, 2),
        counts_by_status=_build_status_counts(histogram, total_surahs * student_count),
    )


async def school_analytics(db: AsyncSession, *, school_id: UUID) -> SchoolAnalytics:
    total_surahs = await analytics_repo.total_surahs(db)
    histogram = await analytics_repo.status_histogram_for_school(db, school_id)
    per_student = await analytics_repo.per_student_aggregates_for_school(db, school_id)

    # Count active students directly (per_student already only contains active)
    student_count = (
        await db.execute(
            select(func.count())
            .select_from(Student)
            .where(Student.school_id == school_id, Student.status == StudentStatus.ACTIVE)
        )
    ).scalar_one()

    if student_count and total_surahs:
        avg_mastery = (
            sum(mc for _, mc, _ in per_student) / student_count / total_surahs * 100.0
        )
        avg_completion = (
            sum(ap for _, _, ap in per_student) / student_count if per_student else 0.0
        )
    else:
        avg_mastery = 0.0
        avg_completion = 0.0

    return SchoolAnalytics(
        school_id=school_id,
        student_count=student_count,
        avg_mastery_percent=round(avg_mastery, 2),
        avg_completion_pct=round(avg_completion, 2),
        counts_by_status=_build_status_counts(histogram, total_surahs * student_count),
    )
