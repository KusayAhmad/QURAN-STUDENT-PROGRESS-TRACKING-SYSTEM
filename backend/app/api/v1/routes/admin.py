"""Admin-only routes: audit log read, user list + CRUD."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.models.audit_log import AuditEntityType
from app.models.user import User, UserRole
from app.schemas.admin import AdminUserCreate, AdminUserRead, AdminUserUpdate
from app.schemas.audit import AuditLogRead
from app.services import audit_service, user_service

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_only = require_roles(UserRole.ADMIN)


@router.get("/audit-logs", response_model=dict)
async def list_audit_logs(
    db: DbSession,
    user: User = Depends(_admin_only),
    entity_type: AuditEntityType | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items, total = await audit_service.list_for_school(
        db,
        school_id=user.school_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [AuditLogRead.model_validate(item) for item in items],
    }


@router.get("/users", response_model=list[AdminUserRead])
async def list_users(
    db: DbSession, user: User = Depends(_admin_only)
) -> list[AdminUserRead]:
    users = await user_service.list_users(db, school_id=user.school_id)
    return [AdminUserRead.model_validate(u) for u in users]


@router.post(
    "/users", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED
)
async def create_user(
    payload: AdminUserCreate,
    db: DbSession,
    user: User = Depends(_admin_only),
) -> AdminUserRead:
    created = await user_service.create_user(
        db, actor_id=user.id, school_id=user.school_id, data=payload
    )
    await db.commit()
    return AdminUserRead.model_validate(created)


@router.put("/users/{user_id}", response_model=AdminUserRead)
async def update_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    db: DbSession,
    user: User = Depends(_admin_only),
) -> AdminUserRead:
    updated = await user_service.update_user(
        db,
        actor_id=user.id,
        school_id=user.school_id,
        user_id=user_id,
        data=payload,
    )
    await db.commit()
    return AdminUserRead.model_validate(updated)
