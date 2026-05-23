"""Audit log schemas (read-only)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditAction, AuditEntityType


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    school_id: UUID | None
    action: AuditAction
    entity_type: AuditEntityType
    entity_id: str
    old_value: dict | None
    new_value: dict | None
    created_at: datetime
