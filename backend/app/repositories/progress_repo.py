"""Memorization progress data access."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memorization_progress import MemorizationProgress


async def list_for_student(
    db: AsyncSession, student_id: UUID
) -> list[MemorizationProgress]:
    stmt = (
        select(MemorizationProgress)
        .where(MemorizationProgress.student_id == student_id)
        .order_by(MemorizationProgress.surah_id)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_by_student_and_surah(
    db: AsyncSession, student_id: UUID, surah_id: int
) -> MemorizationProgress | None:
    stmt = select(MemorizationProgress).where(
        MemorizationProgress.student_id == student_id,
        MemorizationProgress.surah_id == surah_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_by_id(
    db: AsyncSession, progress_id: UUID
) -> MemorizationProgress | None:
    stmt = select(MemorizationProgress).where(MemorizationProgress.id == progress_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def add(db: AsyncSession, progress: MemorizationProgress) -> MemorizationProgress:
    db.add(progress)
    await db.flush()
    await db.refresh(progress)
    return progress
