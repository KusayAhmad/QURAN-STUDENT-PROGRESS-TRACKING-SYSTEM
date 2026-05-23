"""Student data access (tenant-scoped by school_id)."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student, StudentStatus


async def list_for_school(
    db: AsyncSession,
    *,
    school_id: UUID,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Student], int]:
    stmt = select(Student).where(Student.school_id == school_id)
    if not include_archived:
        stmt = stmt.where(Student.status != StudentStatus.ARCHIVED)
    if search:
        stmt = stmt.where(Student.full_name.ilike(f"%{search}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Student.full_name).limit(limit).offset(offset)
    items = (await db.execute(stmt)).scalars().all()
    return list(items), total


async def get_for_school(
    db: AsyncSession, *, school_id: UUID, student_id: UUID
) -> Student | None:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    return result.scalar_one_or_none()


async def add(db: AsyncSession, student: Student) -> Student:
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


async def delete(db: AsyncSession, student: Student) -> None:
    await db.delete(student)
    await db.flush()
