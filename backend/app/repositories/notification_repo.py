"""Notification data access (per-user inbox)."""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def add(db: AsyncSession, notification: Notification) -> Notification:
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.recipient_user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit).offset(offset)
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def unread_count(db: AsyncSession, *, user_id: UUID) -> int:
    return (
        await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
    ).scalar_one()


async def get_for_user(
    db: AsyncSession, *, user_id: UUID, notification_id: UUID
) -> Notification | None:
    return (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id,
            )
        )
    ).scalar_one_or_none()


async def mark_read(db: AsyncSession, notification: Notification) -> Notification:
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, *, user_id: UUID) -> int:
    """Returns number of rows updated."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(Notification)
        .where(
            Notification.recipient_user_id == user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=now)
    )
    return result.rowcount or 0
