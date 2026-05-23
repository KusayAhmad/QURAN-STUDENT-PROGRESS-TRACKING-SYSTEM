"""Per-user notification inbox routes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.repositories import notification_repo
from app.schemas.notification import NotificationRead, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=dict)
async def list_notifications(
    db: DbSession,
    user: CurrentUser,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    items, total = await notification_repo.list_for_user(
        db,
        user_id=user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [NotificationRead.model_validate(n) for n in items],
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(db: DbSession, user: CurrentUser) -> UnreadCountResponse:
    count = await notification_repo.unread_count(db, user_id=user.id)
    return UnreadCountResponse(unread=count)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: UUID, db: DbSession, user: CurrentUser
) -> NotificationRead:
    notif = await notification_repo.get_for_user(
        db, user_id=user.id, notification_id=notification_id
    )
    if notif is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    notif = await notification_repo.mark_read(db, notif)
    await db.commit()
    return NotificationRead.model_validate(notif)


@router.post("/read-all", response_model=dict)
async def mark_all_read(db: DbSession, user: CurrentUser) -> dict:
    updated = await notification_repo.mark_all_read(db, user_id=user.id)
    await db.commit()
    return {"updated": updated}
