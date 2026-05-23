"""Observation data access."""
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observation import Observation


async def list_for_student(
    db: AsyncSession, student_id: UUID, limit: int = 50, offset: int = 0
) -> list[Observation]:
    stmt = (
        select(Observation)
        .where(Observation.student_id == student_id)
        .order_by(desc(Observation.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())


async def count_for_student(db: AsyncSession, student_id: UUID) -> int:
    return (
        await db.execute(
            select(func.count())
            .select_from(Observation)
            .where(Observation.student_id == student_id)
        )
    ).scalar_one()


async def get_by_id(db: AsyncSession, observation_id: UUID) -> Observation | None:
    return (
        await db.execute(select(Observation).where(Observation.id == observation_id))
    ).scalar_one_or_none()


async def add(db: AsyncSession, observation: Observation) -> Observation:
    db.add(observation)
    await db.flush()
    await db.refresh(observation)
    return observation


async def delete(db: AsyncSession, observation: Observation) -> None:
    await db.delete(observation)
    await db.flush()
