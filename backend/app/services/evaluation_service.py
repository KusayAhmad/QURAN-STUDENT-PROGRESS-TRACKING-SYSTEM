"""Evaluation business logic. Tenant-scoped via student's school. Audited."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType
from app.models.evaluation import Evaluation
from app.repositories import evaluation_repo, student_repo
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate
from app.services import audit_service, notification_service

_AUDIT_FIELDS = (
    "student_id",
    "teacher_id",
    "type",
    "exam_date",
    "tajweed_score",
    "accuracy_score",
    "fluency_score",
    "retention_score",
    "speed_score",
    "confidence_score",
    "overall_score",
    "notes",
)


async def list_evaluations(
    db: AsyncSession, *, school_id: UUID, student_id: UUID, limit: int, offset: int
) -> tuple[list[Evaluation], int]:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    items = await evaluation_repo.list_for_student(db, student_id, limit=limit, offset=offset)
    total = await evaluation_repo.count_for_student(db, student_id)
    return items, total


async def create_evaluation(
    db: AsyncSession,
    *,
    school_id: UUID,
    student_id: UUID,
    teacher_id: UUID,
    data: EvaluationCreate,
) -> Evaluation:
    student = await student_repo.get_for_school(db, school_id=school_id, student_id=student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    payload = data.model_dump()
    # If overall_score is omitted but per-axis scores exist, compute the mean.
    axis_scores = [
        payload.get(k)
        for k in (
            "tajweed_score",
            "accuracy_score",
            "fluency_score",
            "retention_score",
            "speed_score",
            "confidence_score",
        )
        if payload.get(k) is not None
    ]
    if payload.get("overall_score") is None and axis_scores:
        payload["overall_score"] = round(sum(axis_scores) / len(axis_scores))

    evaluation = Evaluation(student_id=student_id, teacher_id=teacher_id, **payload)
    evaluation = await evaluation_repo.add(db, evaluation)

    await audit_service.record(
        db,
        actor_id=teacher_id,
        school_id=school_id,
        action=AuditAction.CREATE,
        entity_type=AuditEntityType.EVALUATION,
        entity_id=evaluation.id,
        new_value=audit_service.snapshot(evaluation, _AUDIT_FIELDS),
    )
    await notification_service.notify_low_evaluation(
        db, student=student, evaluation=evaluation, actor_id=teacher_id
    )
    return evaluation


async def get_evaluation(
    db: AsyncSession, *, school_id: UUID, evaluation_id: UUID
) -> Evaluation:
    evaluation = await evaluation_repo.get_by_id(db, evaluation_id)
    if evaluation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluation not found")
    # Tenant check via student
    student = await student_repo.get_for_school(
        db, school_id=school_id, student_id=evaluation.student_id
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluation not found")
    return evaluation


async def update_evaluation(
    db: AsyncSession,
    *,
    actor_id: UUID,
    school_id: UUID,
    evaluation_id: UUID,
    data: EvaluationUpdate,
) -> Evaluation:
    evaluation = await get_evaluation(db, school_id=school_id, evaluation_id=evaluation_id)
    old_value = audit_service.snapshot(evaluation, _AUDIT_FIELDS)

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(evaluation, field, value)
    await db.flush()
    await db.refresh(evaluation)

    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.UPDATE,
        entity_type=AuditEntityType.EVALUATION,
        entity_id=evaluation.id,
        old_value=old_value,
        new_value=audit_service.snapshot(evaluation, _AUDIT_FIELDS),
    )
    return evaluation


async def delete_evaluation(
    db: AsyncSession, *, actor_id: UUID, school_id: UUID, evaluation_id: UUID
) -> None:
    evaluation = await get_evaluation(db, school_id=school_id, evaluation_id=evaluation_id)
    old_value = audit_service.snapshot(evaluation, _AUDIT_FIELDS)
    await evaluation_repo.delete(db, evaluation)
    await audit_service.record(
        db,
        actor_id=actor_id,
        school_id=school_id,
        action=AuditAction.DELETE,
        entity_type=AuditEntityType.EVALUATION,
        entity_id=evaluation_id,
        old_value=old_value,
    )
