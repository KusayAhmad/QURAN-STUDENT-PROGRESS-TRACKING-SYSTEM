"""Student CRUD routes (tenant-scoped)."""
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, SchoolUser
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=dict)
async def list_students(
    db: DbSession,
    user: SchoolUser,
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items, total = await student_service.list_students(
        db,
        school_id=user.school_id,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [StudentRead.model_validate(s) for s in items],
    }


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate, db: DbSession, user: SchoolUser
) -> StudentRead:
    student = await student_service.create_student(
        db, school_id=user.school_id, data=payload
    )
    await db.commit()
    return StudentRead.model_validate(student)


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: UUID, db: DbSession, user: SchoolUser
) -> StudentRead:
    student = await student_service.get_student(
        db, school_id=user.school_id, student_id=student_id
    )
    return StudentRead.model_validate(student)


@router.put("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: UUID, payload: StudentUpdate, db: DbSession, user: SchoolUser
) -> StudentRead:
    student = await student_service.update_student(
        db, school_id=user.school_id, student_id=student_id, data=payload
    )
    await db.commit()
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", response_model=StudentRead)
async def archive_student(
    student_id: UUID, db: DbSession, user: SchoolUser
) -> StudentRead:
    """Soft delete (archive). Hard delete is intentionally not exposed."""
    student = await student_service.archive_student(
        db, school_id=user.school_id, student_id=student_id
    )
    await db.commit()
    return StudentRead.model_validate(student)
