"""Audit service: record() is called by every mutating service.

Design choice: explicit calls from each service rather than SQLAlchemy event
listeners. The trade-off is slightly more boilerplate in services, but:
  - actor_id is unambiguous (no ContextVar tricks)
  - we can write human-readable diffs instead of raw column maps
  - audit calls are easy to assert in tests
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditEntityType, AuditLog
from app.repositories import audit_log_repo


def _serialize(value: Any) -> Any:
    """JSON-safe-ify common types used in our models."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (UUID, date, datetime)):
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value)
    if hasattr(value, "value"):  # Enum
        return value.value
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    return str(value)


def snapshot(obj: object, fields: tuple[str, ...]) -> dict[str, Any]:
    """Build a JSON-safe snapshot of selected attributes from a model instance."""
    return {f: _serialize(getattr(obj, f, None)) for f in fields}


async def record(
    db: AsyncSession,
    *,
    actor_id: UUID | None,
    school_id: UUID | None,
    action: AuditAction,
    entity_type: AuditEntityType,
    entity_id: str | UUID,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        school_id=school_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_value=old_value,
        new_value=new_value,
    )
    return await audit_log_repo.add(db, log)


async def list_for_school(
    db: AsyncSession,
    *,
    school_id: UUID,
    entity_type: AuditEntityType | None,
    entity_id: str | None,
    limit: int,
    offset: int,
):
    return await audit_log_repo.list_for_school(
        db,
        school_id=school_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
