"""FastAPI dependencies: DB session, current user, role guards."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories import user_repo

_settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{_settings.api_v1_prefix}/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except JWTError as e:
        raise credentials_exc from e

    if payload.get("type") != "access":
        raise credentials_exc

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exc

    user = await user_repo.get_by_id(db, UUID(sub))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    async def _checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _checker


async def require_school_user(user: CurrentUser) -> User:
    """Most endpoints are tenant-scoped: caller must belong to a school."""
    if user.school_id is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Account is not attached to a school",
        )
    return user


SchoolUser = Annotated[User, Depends(require_school_user)]
