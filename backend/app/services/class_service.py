"""Class management. Tenant-scoped; writes are admin-only (enforced at route)."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType
from app.models.class_ import Class
from app.repositories import class_repo
from app.schemas.class_ import ClassCreate, ClassUpdate
from app.services import audit_service

_AUDIT_FIELDS = ("name", "academic_year", "teacher_id", "school_id")


async def list_classes(db: AsyncSession, *, school_id: UUID) -> list[Class]:
    return await class_repo.list_for_school(db, school_id)


async def get_class(db: AsyncSession, *, school_id: UUID, class_id: UUID) -> Class:
    klass = await class_repo.get_for_school(db, school_id=school_id, class_id=class_id)
    if klass is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return klass


async def create_class(
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, data: ClassCreate
) -> Class:
    klass = Class(
        school_id=school_id,
        name=data.name,
        academic_year=data.academic_year,
        teacher_id=data.teacher_id,
    )
    klass = await class_repo.add(db, klass)
    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.CREATE,
        entity_type=AuditEntityType.CLASS,
        entity_id=klass.id,
        new_value=audit_service.snapshot(klass, _AUDIT_FIELDS),
    )
    return klass


async def update_class(
    db: AsyncSession,
    *,
    actor_id: UUID,
    school_id: UUID,
    class_id: UUID,
    data: ClassUpdate,
) -> Class:
    klass = await get_class(db, school_id=school_id, class_id=class_id)
    old_value = audit_service.snapshot(klass, _AUDIT_FIELDS)

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(klass, field, value)
    await db.flush()
    await db.refresh(klass)

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.CLASS,
        entity_id=klass.id,
        old_value=old_value,
        new_value=audit_service.snapshot(klass, _AUDIT_FIELDS),
    )
    return klass


async def delete_class(
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, class_id: UUID
) -> None:
    klass = await get_class(db, school_id=school_id, class_id=class_id)
    old_value = audit_service.snapshot(klass, _AUDIT_FIELDS)
    await class_repo.delete(db, klass)
    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.DELETE,
        entity_type=AuditEntityType.CLASS,
        entity_id=class_id,
        old_value=old_value,
    )
