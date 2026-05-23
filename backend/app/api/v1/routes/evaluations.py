"""Evaluation routes."""
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, SchoolUser
from app.schemas.evaluation import EvaluationCreate, EvaluationRead, EvaluationUpdate
from app.services import evaluation_service

router = APIRouter(tags=["evaluations"])


@router.get("/students/{student_id}/evaluations", response_model=dict)
async def list_evaluations(
    student_id: UUID,
    db: DbSession,
    user: SchoolUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items, total = await evaluation_service.list_evaluations(
        db, school_id=user.school_id, student_id=student_id, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [EvaluationRead.model_validate(e) for e in items],
    }


@router.post(
    "/students/{student_id}/evaluations",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation(
    student_id: UUID,
    payload: EvaluationCreate,
    db: DbSession,
    user: SchoolUser,
) -> EvaluationRead:
    evaluation = await evaluation_service.create_evaluation(
        db,
        school_id=user.school_id,
        student_id=student_id,
        teacher_id=user.id,
        data=payload,
    )
    await db.commit()
    return EvaluationRead.model_validate(evaluation)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
    evaluation_id: UUID, db: DbSession, user: SchoolUser
) -> EvaluationRead:
    evaluation = await evaluation_service.get_evaluation(
        db, school_id=user.school_id, evaluation_id=evaluation_id
    )
    return EvaluationRead.model_validate(evaluation)


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: UUID,
    payload: EvaluationUpdate,
    db: DbSession,
    user: SchoolUser,
) -> EvaluationRead:
    evaluation = await evaluation_service.update_evaluation(
        db, school_id=user.school_id, evaluation_id=evaluation_id, data=payload
    )
    await db.commit()
    return EvaluationRead.model_validate(evaluation)


@router.delete("/evaluations/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: UUID, db: DbSession, user: SchoolUser
) -> None:
    await evaluation_service.delete_evaluation(
        db, school_id=user.school_id, evaluation_id=evaluation_id
    )
    await db.commit()
