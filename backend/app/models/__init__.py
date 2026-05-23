"""SQLAlchemy ORM models. Importing this module registers all tables on Base.metadata."""
from app.models.audit_log import AuditAction, AuditEntityType, AuditLog
from app.models.class_ import Class
from app.models.evaluation import Evaluation, EvaluationType
from app.models.memorization_progress import MemorizationProgress, MemorizationStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin
from app.models.notification import Notification, NotificationType
from app.models.observation import Observation, ObservationType
from app.models.progress_history import ProgressHistory
from app.models.school import School
from app.models.student import Student, StudentGender, StudentStatus
from app.models.surah import QuranSurah
from app.models.user import User, UserRole

__all__ = [
    "AuditAction",
    "AuditEntityType",
    "AuditLog",
    "Class",
    "Evaluation",
    "EvaluationType",
    "MemorizationProgress",
    "MemorizationStatus",
    "Notification",
    "NotificationType",
    "Observation",
    "ObservationType",
    "ProgressHistory",
    "QuranSurah",
    "School",
    "Student",
    "StudentGender",
    "StudentStatus",
    "TimestampMixin",
    "UUIDPKMixin",
    "User",
    "UserRole",
]
