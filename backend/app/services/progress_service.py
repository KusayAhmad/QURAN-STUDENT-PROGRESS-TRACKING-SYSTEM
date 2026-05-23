"""Memorization progress business logic."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memorization_progress import MemorizationProgress
from app.repositories import progress_repo, student_repo, surah_repo
from app.schemas.progress import ProgressUpdate, ProgressUpsert


async def list_progress(
    db: AsyncSession, *, school_id: UUID, student_id: UUID
) -> list[MemorizationProgress]:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return await progress_repo.list_for_student(db, student_id)


async def upsert_progress(
    db: AsyncSession,
    *,
    school_id: UUID,
    student_id: UUID,
    teacher_id: UUID,
    data: ProgressUpsert,
) -> MemorizationProgress:
    """Create or update the progress row for (student, surah). Replaces Excel cell-edit."""
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    surah = await surah_repo.get_by_id(db, data.surah_id)
    if surah is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Surah not found")

    existing = await progress_repo.get_by_student_and_surah(db, student_id, data.surah_id)
    if existing is None:
        existing = MemorizationProgress(
            student_id=student_id,
            surah_id=data.surah_id,
            teacher_id=teacher_id,
            status=data.status,
            score=data.score,
            completion_percent=data.completion_percent,
            notes=data.notes,
            last_reviewed_at=data.last_reviewed_at,
        )
        return await progress_repo.add(db, existing)

    existing.status = data.status
    existing.score = data.score
    existing.completion_percent = data.completion_percent
    existing.notes = data.notes
    existing.last_reviewed_at = data.last_reviewed_at
    existing.teacher_id = teacher_id
    await db.flush()
    await db.refresh(existing)
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

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(progress, field, value)
    progress.teacher_id = teacher_id
    await db.flush()
    await db.refresh(progress)
    return progress
