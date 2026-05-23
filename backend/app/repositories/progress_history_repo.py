"""ProgressHistory data access (append + per-(student,surah) timeline)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress_history import ProgressHistory


async def add(db: AsyncSession, row: ProgressHistory) -> ProgressHistory:
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def list_for_student_surah(
    db: AsyncSession, student_id: UUID, surah_id: int
) -> list[ProgressHistory]:
    stmt = (
        select(ProgressHistory)
        .where(
            ProgressHistory.student_id == student_id,
            ProgressHistory.surah_id == surah_id,
        )
        .order_by(ProgressHistory.recorded_at)
    )
    return list((await db.execute(stmt)).scalars().all())
