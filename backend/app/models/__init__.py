"""SQLAlchemy ORM models. Importing this module registers all tables on Base.metadata."""
from app.models.class_ import Class
from app.models.memorization_progress import MemorizationProgress, MemorizationStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin
from app.models.school import School
from app.models.student import Student, StudentGender, StudentStatus
from app.models.surah import QuranSurah
from app.models.user import User, UserRole

__all__ = [
    "Class",
    "MemorizationProgress",
    "MemorizationStatus",
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
