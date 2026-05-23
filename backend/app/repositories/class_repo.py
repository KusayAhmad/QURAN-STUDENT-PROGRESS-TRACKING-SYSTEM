"""Class (group of students) data access."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class


async def list_for_school(db: AsyncSession, school_id: UUID) -> list[Class]:
    stmt = select(Class).where(Class.school_id == school_id).order_by(Class.name)
    return list((await db.execute(stmt)).scalars().all())


async def get_for_school(
    db: AsyncSession, *, school_id: UUID, class_id: UUID
) -> Class | None:
    return (
        await db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == school_id)
        )
    ).scalar_one_or_none()


async def add(db: AsyncSession, klass: Class) -> Class:
    db.add(klass)
    await db.flush()
    await db.refresh(klass)
    return klass


async def delete(db: AsyncSession, klass: Class) -> None:
    await db.delete(klass)
    await db.flush()
