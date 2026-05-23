"""Observation routes."""
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, SchoolUser
from app.schemas.observation import ObservationCreate, ObservationRead
from app.services import observation_service

router = APIRouter(tags=["observations"])


@router.get("/students/{student_id}/observations", response_model=dict)
async def list_observations(
    student_id: UUID,
    db: DbSession,
    user: SchoolUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items, total = await observation_service.list_observations(
        db, school_id=user.school_id, student_id=student_id, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [ObservationRead.model_validate(o) for o in items],
    }


@router.post(
    "/students/{student_id}/observations",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_observation(
    student_id: UUID,
    payload: ObservationCreate,
    db: DbSession,
    user: SchoolUser,
) -> ObservationRead:
    obs = await observation_service.create_observation(
        db,
        school_id=user.school_id,
        student_id=student_id,
        teacher_id=user.id,
        data=payload,
    )
    await db.commit()
    return ObservationRead.model_validate(obs)


@router.delete(
    "/observations/{observation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_observation(
    observation_id: UUID, db: DbSession, user: SchoolUser
) -> None:
    await observation_service.delete_observation(
        db, actor_id=user.id, school_id=user.school_id, observation_id=observation_id
    )
    await db.commit()
