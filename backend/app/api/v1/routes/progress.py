"""Memorization progress routes (the Excel matrix replacement)."""
from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import DbSession, SchoolUser
from app.schemas.progress import ProgressRead, ProgressUpdate, ProgressUpsert
from app.services import progress_service

router = APIRouter(tags=["progress"])


@router.get("/students/{student_id}/progress", response_model=list[ProgressRead])
async def list_progress(
    student_id: UUID, db: DbSession, user: SchoolUser
) -> list[ProgressRead]:
    rows = await progress_service.list_progress(
        db, school_id=user.school_id, student_id=student_id
    )
    return [ProgressRead.model_validate(r) for r in rows]


@router.post(
    "/students/{student_id}/progress",
    response_model=ProgressRead,
    status_code=status.HTTP_200_OK,
)
async def upsert_progress(
    student_id: UUID,
    payload: ProgressUpsert,
    db: DbSession,
    user: SchoolUser,
) -> ProgressRead:
    """Create or update the (student, surah) progress row.

    Idempotent: calling twice with same surah_id updates the existing row.
    """
    row = await progress_service.upsert_progress(
        db,
        school_id=user.school_id,
        student_id=student_id,
        teacher_id=user.id,
        data=payload,
    )
    await db.commit()
    return ProgressRead.model_validate(row)


@router.put("/progress/{progress_id}", response_model=ProgressRead)
async def update_progress(
    progress_id: UUID,
    payload: ProgressUpdate,
    db: DbSession,
    user: SchoolUser,
) -> ProgressRead:
    row = await progress_service.update_progress(
        db,
        school_id=user.school_id,
        progress_id=progress_id,
        teacher_id=user.id,
        data=payload,
    )
    await db.commit()
    return ProgressRead.model_validate(row)
