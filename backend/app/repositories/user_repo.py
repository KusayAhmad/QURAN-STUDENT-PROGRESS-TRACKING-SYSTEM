"""User data access."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_for_school(db: AsyncSession, school_id: UUID) -> list[User]:
    return list(
        (
            await db.execute(
                select(User).where(User.school_id == school_id).order_by(User.email)
            )
        )
        .scalars()
        .all()
    )
