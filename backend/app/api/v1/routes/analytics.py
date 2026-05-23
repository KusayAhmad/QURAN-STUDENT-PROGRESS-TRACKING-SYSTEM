"""Analytics routes — read-only KPIs."""
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession, SchoolUser
from app.schemas.analytics import ClassAnalytics, SchoolAnalytics, StudentAnalytics
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/student/{student_id}", response_model=StudentAnalytics)
async def student_analytics(
    student_id: UUID, db: DbSession, user: SchoolUser
) -> StudentAnalytics:
    return await analytics_service.student_analytics(
        db, school_id=user.school_id, student_id=student_id
    )


@router.get("/class/{class_id}", response_model=ClassAnalytics)
async def class_analytics(
    class_id: UUID, db: DbSession, user: SchoolUser
) -> ClassAnalytics:
    return await analytics_service.class_analytics(
        db, school_id=user.school_id, class_id=class_id
    )


@router.get("/school", response_model=SchoolAnalytics)
async def school_analytics(db: DbSession, user: SchoolUser) -> SchoolAnalytics:
    return await analytics_service.school_analytics(db, school_id=user.school_id)
