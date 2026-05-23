"""Auth routes: login, refresh, me."""
from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import CurrentUser as CurrentUserSchema
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    user = await auth_service.authenticate(db, payload.email, payload.password)
    access, refresh = auth_service.issue_token_pair(user)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    access, refresh = await auth_service.refresh_access_token(db, payload.refresh_token)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=CurrentUserSchema)
async def me(user: CurrentUser) -> CurrentUserSchema:
    return CurrentUserSchema(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        school_id=user.school_id,
        is_active=user.is_active,
    )
