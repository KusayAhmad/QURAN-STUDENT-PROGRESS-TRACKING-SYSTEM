"""AuditLog data access (append + tenant-scoped list)."""
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditEntityType, AuditLog


async def add(db: AsyncSession, log: AuditLog) -> AuditLog:
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def list_for_school(
    db: AsyncSession,
    *,
    school_id: UUID,
    entity_type: AuditEntityType | None = None,
    entity_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog).where(AuditLog.school_id == school_id)
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    items = list((await db.execute(stmt)).scalars().all())
    return items, total
