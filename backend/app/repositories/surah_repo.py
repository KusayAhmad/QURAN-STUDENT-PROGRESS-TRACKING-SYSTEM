"""Surah read-only data access."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.surah import QuranSurah


async def list_all(db: AsyncSession) -> list[QuranSurah]:
    result = await db.execute(select(QuranSurah).order_by(QuranSurah.surah_order))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, surah_id: int) -> QuranSurah | None:
    result = await db.execute(select(QuranSurah).where(QuranSurah.id == surah_id))
    return result.scalar_one_or_none()
