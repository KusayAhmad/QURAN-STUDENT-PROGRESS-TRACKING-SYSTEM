"""Student business logic (tenant-scoped)."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.repositories import student_repo
from app.schemas.student import StudentCreate, StudentUpdate


async def list_students(
    db: AsyncSession,
    *,
    school_id: UUID,
    search: str | None,
    include_archived: bool,
    limit: int,
    offset: int,
) -> tuple[list[Student], int]:
    return await student_repo.list_for_school(
        db,
        school_id=school_id,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


async def get_student(db: AsyncSession, *, school_id: UUID, student_id: UUID) -> Student:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return student


async def create_student(
    db: AsyncSession, *, school_id: UUID, data: StudentCreate
) -> Student:
    student = Student(
        school_id=school_id,
        full_name=data.full_name,
        gender=data.gender,
        birth_date=data.birth_date,
        enrollment_date=data.enrollment_date,
        guardian_name=data.guardian_name,
        guardian_phone=data.guardian_phone,
        notes=data.notes,
        class_id=data.class_id,
    )
    return await student_repo.add(db, student)


async def update_student(
    db: AsyncSession, *, school_id: UUID, student_id: UUID, data: StudentUpdate
) -> Student:
    student = await get_student(db, school_id=school_id, student_id=student_id)
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(student, field, value)
    await db.flush()
    await db.refresh(student)
    return student


async def archive_student(
    db: AsyncSession, *, school_id: UUID, student_id: UUID
) -> Student:
    """Soft delete: mark archived rather than hard delete (per blueprint §12-I)."""
    from app.models.student import StudentStatus

    student = await get_student(db, school_id=school_id, student_id=student_id)
    student.status = StudentStatus.ARCHIVED
    await db.flush()
    await db.refresh(student)
    return student
