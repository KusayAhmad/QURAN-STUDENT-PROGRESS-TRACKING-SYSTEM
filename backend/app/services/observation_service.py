"""Observation business logic. Tenant-scoped via the student's school. Audited."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType
from app.models.observation import Observation
from app.repositories import observation_repo, student_repo
from app.schemas.observation import ObservationCreate
from app.services import audit_service

_AUDIT_FIELDS = ("student_id", "teacher_id", "type", "message")


async def list_observations(
    db: AsyncSession, *, school_id: UUID, student_id: UUID, limit: int, offset: int
) -> tuple[list[Observation], int]:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    items = await observation_repo.list_for_student(db, student_id, limit=limit, offset=offset)
    total = await observation_repo.count_for_student(db, student_id)
    return items, total


async def create_observation(
    db: AsyncSession,
    *,
    school_id: UUID,
    student_id: UUID,
    teacher_id: UUID,
    data: ObservationCreate,
) -> Observation:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    obs = Observation(
        student_id=student_id, teacher_id=teacher_id, type=data.type, message=data.message
    )
    obs = await observation_repo.add(db, obs)
    await audit_service.record(
        db,
        actor_id=teacher_id,
        school_id=school_id,
        action=AuditAction.CREATE,
        entity_type=AuditEntityType.OBSERVATION,
        entity_id=obs.id,
        new_value=audit_service.snapshot(obs, _AUDIT_FIELDS),
    )
    return obs


async def delete_observation(
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, observation_id: UUID
) -> None:
    obs = await observation_repo.get_by_id(db, observation_id)
    if obs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Observation not found")
    student = await student_repo.get_for_school(
        db, school_id=school_id, student_id=obs.student_id
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Observation not found")

    old_value = audit_service.snapshot(obs, _AUDIT_FIELDS)
    await observation_repo.delete(db, obs)
    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.DELETE,
        entity_type=AuditEntityType.OBSERVATION,
        entity_id=observation_id,
        old_value=old_value,
    )
