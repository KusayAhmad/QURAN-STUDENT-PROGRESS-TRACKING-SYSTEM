"""Aggregate queries used by AnalyticsService.

These are read-only and SHOULD be the only place we run GROUP BY / COUNT queries
across the schema. Services compose them; routers don't touch them.
"""
from uuid import UUID

from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.memorization_progress import MemorizationProgress, MemorizationStatus
from app.models.student import Student, StudentStatus
from app.models.surah import QuranSurah


async def total_surahs(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(QuranSurah))).scalar_one()


async def status_histogram_for_student(
    db: AsyncSession, student_id: UUID
) -> dict[MemorizationStatus, int]:
    rows = (
        await db.execute(
            select(MemorizationProgress.status, func.count())
            .where(MemorizationProgress.student_id == student_id)
            .group_by(MemorizationProgress.status)
        )
    ).all()
    return {status: int(count) for status, count in rows}


async def avg_completion_for_student(db: AsyncSession, student_id: UUID) -> float:
    """Mean of completion_percent across recorded surahs (0.0 if none)."""
    val = (
        await db.execute(
            select(func.avg(MemorizationProgress.completion_percent))
            .where(MemorizationProgress.student_id == student_id)
        )
    ).scalar_one()
    return float(val) if val is not None else 0.0


async def surah_ids_by_status(
    db: AsyncSession, student_id: UUID, status: MemorizationStatus
) -> list[int]:
    rows = (
        await db.execute(
            select(MemorizationProgress.surah_id)
            .where(
                MemorizationProgress.student_id == student_id,
                MemorizationProgress.status == status,
            )
            .order_by(MemorizationProgress.surah_id)
        )
    ).scalars().all()
    return list(rows)


async def last_activity_for_student(db: AsyncSession, student_id: UUID):
    """Latest updated_at across progress + evaluations for the student."""
    progress_max = (
        await db.execute(
            select(func.max(MemorizationProgress.updated_at)).where(
                MemorizationProgress.student_id == student_id
            )
        )
    ).scalar_one()
    eval_max = (
        await db.execute(
            select(func.max(Evaluation.updated_at)).where(Evaluation.student_id == student_id)
        )
    ).scalar_one()
    candidates = [c for c in (progress_max, eval_max) if c is not None]
    return max(candidates) if candidates else None


async def status_histogram_for_school(
    db: AsyncSession, school_id: UUID
) -> dict[MemorizationStatus, int]:
    """Aggregate progress histogram across all active students in a school."""
    rows = (
        await db.execute(
            select(MemorizationProgress.status, func.count())
            .join(Student, Student.id == MemorizationProgress.student_id)
            .where(
                Student.school_id == school_id,
                Student.status == StudentStatus.ACTIVE,
            )
            .group_by(MemorizationProgress.status)
        )
    ).all()
    return {status: int(count) for status, count in rows}


async def status_histogram_for_class(
    db: AsyncSession, class_id: UUID
) -> dict[MemorizationStatus, int]:
    rows = (
        await db.execute(
            select(MemorizationProgress.status, func.count())
            .join(Student, Student.id == MemorizationProgress.student_id)
            .where(
                Student.class_id == class_id,
                Student.status == StudentStatus.ACTIVE,
            )
            .group_by(MemorizationProgress.status)
        )
    ).all()
    return {status: int(count) for status, count in rows}


async def per_student_aggregates_for_class(
    db: AsyncSession, class_id: UUID
) -> list[tuple[UUID, int, float]]:
    """Per active student in the class: (student_id, mastered_count, avg_completion_pct).

    Students with no progress rows still appear, with mastered=0 and avg=0.
    """
    mastered_expr = case(
        (MemorizationProgress.status == MemorizationStatus.MASTERED, literal(1)), else_=literal(0)
    )
    stmt = (
        select(
            Student.id,
            func.coalesce(func.sum(mastered_expr), 0).label("mastered_count"),
            func.coalesce(func.avg(MemorizationProgress.completion_percent), 0).label("avg_pct"),
        )
        .select_from(Student)
        .outerjoin(MemorizationProgress, MemorizationProgress.student_id == Student.id)
        .where(
            Student.class_id == class_id,
            Student.status == StudentStatus.ACTIVE,
        )
        .group_by(Student.id)
    )
    return [
        (sid, int(mc or 0), float(ap or 0)) for sid, mc, ap in (await db.execute(stmt)).all()
    ]


async def per_student_aggregates_for_school(
    db: AsyncSession, school_id: UUID
) -> list[tuple[UUID, int, float]]:
    mastered_expr = case(
        (MemorizationProgress.status == MemorizationStatus.MASTERED, literal(1)), else_=literal(0)
    )
    stmt = (
        select(
            Student.id,
            func.coalesce(func.sum(mastered_expr), 0).label("mastered_count"),
            func.coalesce(func.avg(MemorizationProgress.completion_percent), 0).label("avg_pct"),
        )
        .select_from(Student)
        .outerjoin(MemorizationProgress, MemorizationProgress.student_id == Student.id)
        .where(
            Student.school_id == school_id,
            Student.status == StudentStatus.ACTIVE,
        )
        .group_by(Student.id)
    )
    return [
        (sid, int(mc or 0), float(ap or 0)) for sid, mc, ap in (await db.execute(stmt)).all()
    ]
