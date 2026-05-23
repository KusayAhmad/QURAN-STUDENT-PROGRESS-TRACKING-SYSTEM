"""AuditLog model — append-only record of mutating actions.

One row per mutation. Tenant-scoped via `school_id` so queries stay fast.
`old_value` and `new_value` are JSON snapshots (NULL for CREATE / DELETE
respectively).
"""
import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import GUID, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.user import User


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"


class AuditEntityType(str, enum.Enum):
    STUDENT = "STUDENT"
    PROGRESS = "PROGRESS"
    EVALUATION = "EVALUATION"
    OBSERVATION = "OBSERVATION"
    CLASS = "CLASS"
    USER = "USER"


class AuditLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    school_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    entity_type: Mapped[AuditEntityType] = mapped_column(
        Enum(AuditEntityType, name="audit_entity_type"), nullable=False, index=True
    )
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_id])
    school: Mapped["School | None"] = relationship(foreign_keys=[school_id])
