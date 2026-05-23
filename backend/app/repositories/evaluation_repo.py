"""Evaluation data access."""
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation


async def list_for_student(
    db: AsyncSession, student_id: UUID, limit: int = 50, offset: int = 0
) -> list[Evaluation]:
    stmt = (
        select(Evaluation)
        .where(Evaluation.student_id == student_id)
        .order_by(desc(Evaluation.exam_date), desc(Evaluation.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())


async def count_for_student(db: AsyncSession, student_id: UUID) -> int:
    return (
        await db.execute(
            select(func.count()).select_from(Evaluation).where(Evaluation.student_id == student_id)
        )
    ).scalar_one()


async def get_by_id(db: AsyncSession, evaluation_id: UUID) -> Evaluation | None:
    return (
        await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    ).scalar_one_or_none()


async def add(db: AsyncSession, evaluation: Evaluation) -> Evaluation:
    db.add(evaluation)
    await db.flush()
    await db.refresh(evaluation)
    return evaluation


async def delete(db: AsyncSession, evaluation: Evaluation) -> None:
    await db.delete(evaluation)
    await db.flush()


async def avg_overall_score_for_student(
    db: AsyncSession, student_id: UUID, last_n: int = 5
) -> tuple[float | None, int]:
    """Return (avg_overall_score, count) over the most recent ``last_n`` evals."""
    sub = (
        select(Evaluation.overall_score)
        .where(
            Evaluation.student_id == student_id,
            Evaluation.overall_score.is_not(None),
        )
        .order_by(desc(Evaluation.exam_date), desc(Evaluation.created_at))
        .limit(last_n)
        .subquery()
    )
    row = (
        await db.execute(
            select(func.avg(sub.c.overall_score), func.count()).select_from(sub)
        )
    ).one()
    avg = row[0]
    return (float(avg) if avg is not None else None), int(row[1])
