"""Memorization progress business logic.

Every successful write also appends a row to `progress_history` and an entry
to `audit_logs`. This is what powers the per-surah timeline endpoint.
"""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType
from app.models.memorization_progress import MemorizationProgress
from app.models.progress_history import ProgressHistory
from app.repositories import progress_history_repo, progress_repo, student_repo, surah_repo
from app.schemas.progress import ProgressUpdate, ProgressUpsert
from app.services import audit_service

_AUDIT_FIELDS = (
    "student_id",
    "surah_id",
    "status",
    "score",
    "completion_percent",
    "notes",
    "last_reviewed_at",
    "teacher_id",
)


async def _append_history(
    db: AsyncSession, *, progress: MemorizationProgress, action: AuditAction
) -> None:
    await progress_history_repo.add(
        db,
        ProgressHistory(
            progress_id=progress.id,
            student_id=progress.student_id,
            surah_id=progress.surah_id,
            teacher_id=progress.teacher_id,
            status=progress.status,
            score=progress.score,
            completion_percent=progress.completion_percent,
            notes=progress.notes,
            action=action,
        ),
    )


async def list_progress(
    db: AsyncSession, *, school_id: UUID, student_id: UUID
) -> list[MemorizationProgress]:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return await progress_repo.list_for_student(db, student_id)


async def list_history_for_surah(
    db: AsyncSession, *, school_id: UUID, student_id: UUID, surah_id: int
) -> list[ProgressHistory]:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return await progress_history_repo.list_for_student_surah(db, student_id, surah_id)


async def upsert_progress(
    db: AsyncSession,
    *,
    school_id: UUID,
    student_id: UUID,
    teacher_id: UUID,
    data: ProgressUpsert,
) -> MemorizationProgress:
    """Create or update the progress row for (student, surah). Replaces Excel cell-edit.

    Side effects: appends to progress_history + audit_logs.
    """
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    surah = await surah_repo.get_by_id(db, data.surah_id)
    if surah is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Surah not found")

    existing = await progress_repo.get_by_student_and_surah(db, student_id, data.surah_id)
    if existing is None:
        new_row = MemorizationProgress(
            student_id=student_id,
            surah_id=data.surah_id,
            teacher_id=teacher_id,
            status=data.status,
            score=data.score,
            completion_percent=data.completion_percent,
            notes=data.notes,
            last_reviewed_at=data.last_reviewed_at,
        )
        new_row = await progress_repo.add(db, new_row)
        await _append_history(db, progress=new_row, action=AuditAction.CREATE)
        await audit_service.record(
            db,
            actor_id=teacher_id,
            school_id=school_id,
            action=AuditAction.CREATE,
            entity_type=AuditEntityType.PROGRESS,
            entity_id=new_row.id,
            new_value=audit_service.snapshot(new_row, _AUDIT_FIELDS),
        )
        return new_row

    old_value = audit_service.snapshot(existing, _AUDIT_FIELDS)

    existing.status = data.status
    existing.score = data.score
    existing.completion_percent = data.completion_percent
    existing.notes = data.notes
    existing.last_reviewed_at = data.last_reviewed_at
    existing.teacher_id = teacher_id
    await db.flush()
    await db.refresh(existing)

    await _append_history(db, progress=existing, action=AuditAction.UPDATE)
    await audit_service.record(
        db,
        actor_id=teacher_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.PROGRESS,
        entity_id=existing.id,
        old_value=old_value,
        new_value=audit_service.snapshot(existing, _AUDIT_FIELDS),
    )
    return existing


async def update_progress(
    db: AsyncSession,
    *,
    school_id: UUID,
    progress_id: UUID,
    teacher_id: UUID,
    data: ProgressUpdate,
) -> MemorizationProgress:
    progress = await progress_repo.get_by_id(db, progress_id)
    if progress is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")

    # Tenant check via student
    student = await student_repo.get_for_school(
        db, school_id=school_id, student_id=progress.student_id
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")

    old_value = audit_service.snapshot(progress, _AUDIT_FIELDS)

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(progress, field, value)
    progress.teacher_id = teacher_id
    await db.flush()
    await db.refresh(progress)

    await _append_history(db, progress=progress, action=AuditAction.UPDATE)
    await audit_service.record(
        db,
        actor_id=teacher_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.PROGRESS,
        entity_id=progress.id,
        old_value=old_value,
        new_value=audit_service.snapshot(progress, _AUDIT_FIELDS),
    )
    return progress
