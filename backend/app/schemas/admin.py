"""Admin-only schemas (user management read views)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    school_id: UUID | None
    created_at: datetime
    updated_at: datetime
