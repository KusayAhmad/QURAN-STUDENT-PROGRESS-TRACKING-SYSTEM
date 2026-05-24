"""V1 API router aggregator."""
from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    analytics,
    auth,
    classes,
    evaluations,
    notifications,
    observations,
    progress,
    revision,
    students,
    surahs,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(surahs.router)
api_router.include_router(progress.router)
api_router.include_router(evaluations.router)
api_router.include_router(observations.router)
api_router.include_router(analytics.router)
api_router.include_router(classes.router)
api_router.include_router(notifications.router)
api_router.include_router(revision.router)
api_router.include_router(admin.router)
