"""User management business logic (admin-only).

Self-protection: an admin cannot demote or deactivate their own account.
Without this guard, an admin could lock themselves (and potentially their
school) out of the admin surface.
"""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.audit_log import AuditAction, AuditEntityType
from app.models.user import User, UserRole
from app.repositories import user_repo
from app.schemas.admin import AdminUserCreate, AdminUserUpdate
from app.services import audit_service

# Fields included in audit snapshots. Crucially does NOT include password_hash.
_AUDIT_FIELDS = ("name", "email", "role", "is_active", "school_id")


async def list_users(db: AsyncSession, *, school_id: UUID) -> list[User]:
    return await user_repo.list_for_school(db, school_id)


async def create_user(
    db: AsyncSession,
    *,
    actor_id: UUID,
    school_id: UUID,
    data: AdminUserCreate,
) -> User:
    existing = await user_repo.get_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        school_id=school_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.CREATE,
        entity_type=AuditEntityType.USER,
        entity_id=user.id,
        new_value=audit_service.snapshot(user, _AUDIT_FIELDS),
    )
    return user


async def update_user(
    db: AsyncSession,
    *,
    actor_id: UUID,
    school_id: UUID,
    user_id: UUID,
    data: AdminUserUpdate,
) -> User:
    user = await user_repo.get_by_id(db, user_id)
    if user is None or user.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    payload = data.model_dump(exclude_unset=True)

    # Self-protection: admins cannot demote or deactivate their own account.
    if user_id == actor_id:
        if "role" in payload and payload["role"] != user.role:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "You cannot change your own role.",
            )
        if "is_active" in payload and payload["is_active"] is False:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "You cannot deactivate your own account.",
            )

    old_value = audit_service.snapshot(user, _AUDIT_FIELDS)
    password_changed = False

    for field, value in payload.items():
        if field == "password":
            if value:
                user.password_hash = hash_password(value)
                password_changed = True
        else:
            setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    new_value = audit_service.snapshot(user, _AUDIT_FIELDS)
    if password_changed:
        # Don't log the password itself, just a marker so it's auditable.
        new_value["password"] = "***changed***"

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.USER,
        entity_id=user.id,
        old_value=old_value,
        new_value=new_value,
    )
    return user
