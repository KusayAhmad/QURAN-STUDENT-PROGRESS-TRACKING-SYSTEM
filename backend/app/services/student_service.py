"""Student business logic (tenant-scoped, audited)."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType
from app.models.student import Student, StudentStatus
from app.repositories import student_repo
from app.schemas.student import StudentCreate, StudentUpdate
from app.services import audit_service, notification_service

_AUDIT_FIELDS = (
    "full_name",
    "gender",
    "birth_date",
    "enrollment_date",
    "guardian_name",
    "guardian_phone",
    "notes",
    "class_id",
    "status",
    "school_id",
)


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
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, data: StudentCreate
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
    student = await student_repo.add(db, student)
    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.CREATE,
        entity_type=AuditEntityType.STUDENT,
        entity_id=student.id,
        new_value=audit_service.snapshot(student, _AUDIT_FIELDS),
    )
    await notification_service.notify_student_added(
        db, student=student, actor_id=actor_id
    )
    return student


async def update_student(
    db: AsyncSession,
    *,
    actor_id: UUID,
    school_id: UUID,
    student_id: UUID,
    data: StudentUpdate,
) -> Student:
    student = await get_student(db, school_id=school_id, student_id=student_id)
    old_value = audit_service.snapshot(student, _AUDIT_FIELDS)

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(student, field, value)
    await db.flush()
    await db.refresh(student)

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.STUDENT,
        entity_id=student.id,
        old_value=old_value,
        new_value=audit_service.snapshot(student, _AUDIT_FIELDS),
    )
    return student


async def archive_student(
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, student_id: UUID
) -> Student:
    """Soft delete: mark archived rather than hard delete (per blueprint §12-I)."""
    student = await get_student(db, school_id=school_id, student_id=student_id)
    old_value = audit_service.snapshot(student, _AUDIT_FIELDS)

    student.status = StudentStatus.ARCHIVED
    await db.flush()
    await db.refresh(student)

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.ARCHIVE,
        entity_type=AuditEntityType.STUDENT,
        entity_id=student.id,
        old_value=old_value,
        new_value=audit_service.snapshot(student, _AUDIT_FIELDS),
    )
    return student
