"""Notification production + delivery.

For MVP this is in-app only. The `_deliver` indirection means future channels
(email, push) plug in by extending `Notification` rows with delivery tracking
fields rather than rewriting call sites.

Recipient resolution rules:
- For per-student events (progress regression, low evaluation, student added):
  notify the student's class teacher (if any) AND every admin in the school,
  EXCEPT the actor (you don't ping yourself for your own action).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.memorization_progress import MemorizationStatus
from app.models.notification import Notification, NotificationType
from app.models.student import Student
from app.models.user import User, UserRole
from app.repositories import notification_repo


# A "regression" is a transition from STRONG/MASTERED back to WEAK/REVIEW_REQUIRED.
_STRONG_STATES = {MemorizationStatus.STRONG, MemorizationStatus.MASTERED}
_WEAK_STATES = {MemorizationStatus.WEAK, MemorizationStatus.REVIEW_REQUIRED}


def is_regression(old: MemorizationStatus | None, new: MemorizationStatus) -> bool:
    if old is None:
        return False
    return old in _STRONG_STATES and new in _WEAK_STATES


async def _recipients_for_student(
    db: AsyncSession,
    *,
    student: Student,
    actor_id: UUID,
) -> list[UUID]:
    """Class teacher (if any) + all active admins in the school, minus actor."""
    recipient_ids: set[UUID] = set()

    if student.class_id is not None:
        # Get the class's teacher.
        from app.models.class_ import Class

        klass = (
            await db.execute(select(Class).where(Class.id == student.class_id))
        ).scalar_one_or_none()
        if klass is not None and klass.teacher_id is not None:
            recipient_ids.add(klass.teacher_id)

    # All admins in the school.
    admins = (
        await db.execute(
            select(User.id).where(
                User.school_id == student.school_id,
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
            )
        )
    ).scalars().all()
    recipient_ids.update(admins)

    recipient_ids.discard(actor_id)
    return list(recipient_ids)


async def _deliver(
    db: AsyncSession,
    *,
    recipient_id: UUID,
    school_id: UUID | None,
    type: NotificationType,
    title: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> Notification:
    """The single seam where future channels (email/push) will plug in."""
    return await notification_repo.add(
        db,
        Notification(
            recipient_user_id=recipient_id,
            school_id=school_id,
            type=type,
            title=title,
            message=message,
            payload=payload,
        ),
    )


# ---- Trigger functions called from existing services ---------------------


async def notify_progress_regressed(
    db: AsyncSession,
    *,
    student: Student,
    old_status: MemorizationStatus | None,
    new_status: MemorizationStatus,
    surah_name: str,
    actor_id: UUID,
) -> int:
    if not is_regression(old_status, new_status):
        return 0
    recipients = await _recipients_for_student(db, student=student, actor_id=actor_id)
    for rid in recipients:
        await _deliver(
            db,
            recipient_id=rid,
            school_id=student.school_id,
            type=NotificationType.PROGRESS_REGRESSED,
            title=f"{student.full_name} regressed on {surah_name}",
            message=(
                f"{old_status.value if old_status else '—'} → {new_status.value}. "
                "Consider scheduling a review."
            ),
            payload={"student_id": str(student.id), "surah_name": surah_name},
        )
    return len(recipients)


# Score below this on a new evaluation triggers a notification.
LOW_EVALUATION_THRESHOLD = 60


async def notify_low_evaluation(
    db: AsyncSession,
    *,
    student: Student,
    evaluation: Evaluation,
    actor_id: UUID,
) -> int:
    if evaluation.overall_score is None or evaluation.overall_score >= LOW_EVALUATION_THRESHOLD:
        return 0
    recipients = await _recipients_for_student(db, student=student, actor_id=actor_id)
    for rid in recipients:
        await _deliver(
            db,
            recipient_id=rid,
            school_id=student.school_id,
            type=NotificationType.LOW_EVALUATION,
            title=f"Low evaluation for {student.full_name}",
            message=(
                f"Overall score {evaluation.overall_score} on {evaluation.exam_date} "
                f"({evaluation.type.value})."
            ),
            payload={
                "student_id": str(student.id),
                "evaluation_id": str(evaluation.id),
                "score": evaluation.overall_score,
            },
        )
    return len(recipients)


async def notify_student_added(
    db: AsyncSession, *, student: Student, actor_id: UUID
) -> int:
    """Notify every admin in the school except the actor."""
    admins = (
        await db.execute(
            select(User.id).where(
                User.school_id == student.school_id,
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
                User.id != actor_id,
            )
        )
    ).scalars().all()
    for rid in admins:
        await _deliver(
            db,
            recipient_id=rid,
            school_id=student.school_id,
            type=NotificationType.STUDENT_ADDED,
            title=f"New student: {student.full_name}",
            message="A teacher just added a new student.",
            payload={"student_id": str(student.id)},
        )
    return len(admins)
