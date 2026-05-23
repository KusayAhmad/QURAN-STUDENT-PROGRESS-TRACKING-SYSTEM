"""Class CRUD routes. Reads = any school user. Writes = ADMIN."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, SchoolUser, require_roles
from app.models.user import User, UserRole
from app.schemas.class_ import ClassCreate, ClassRead, ClassUpdate
from app.services import class_service

router = APIRouter(prefix="/classes", tags=["classes"])

_admin_only = require_roles(UserRole.ADMIN)


@router.get("", response_model=list[ClassRead])
async def list_classes(db: DbSession, user: SchoolUser) -> list[ClassRead]:
    rows = await class_service.list_classes(db, school_id=user.school_id)
    return [ClassRead.model_validate(r) for r in rows]


@router.get("/{class_id}", response_model=ClassRead)
async def get_class(
    class_id: UUID, db: DbSession, user: SchoolUser
) -> ClassRead:
    klass = await class_service.get_class(
        db, school_id=user.school_id, class_id=class_id
    )
    return ClassRead.model_validate(klass)


@router.post("", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: ClassCreate,
    db: DbSession,
    user: User = Depends(_admin_only),
) -> ClassRead:
    klass = await class_service.create_class(
        db, actor_id=user.id, school_id=user.school_id, data=payload
    )
    await db.commit()
    return ClassRead.model_validate(klass)


@router.put("/{class_id}", response_model=ClassRead)
async def update_class(
    class_id: UUID,
    payload: ClassUpdate,
    db: DbSession,
    user: User = Depends(_admin_only),
) -> ClassRead:
    klass = await class_service.update_class(
        db,
        actor_id=user.id,
        school_id=user.school_id,
        class_id=class_id,
        data=payload,
    )
    await db.commit()
    return ClassRead.model_validate(klass)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: UUID,
    db: DbSession,
    user: User = Depends(_admin_only),
) -> None:
    await class_service.delete_class(
        db, actor_id=user.id, school_id=user.school_id, class_id=class_id
    )
    await db.commit()
