"""Matrix view: returns the full Quran×Student grid for a school."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memorization_progress import MemorizationProgress
from app.models.student import Student, StudentStatus
from app.repositories import surah_repo
from app.schemas.matrix import MatrixCell, MatrixStudent, MatrixView
from app.schemas.surah import SurahRead


async def get_matrix(
    db: AsyncSession,
    *,
    school_id: UUID,
    class_id: UUID | None,
    include_archived: bool,
) -> MatrixView:
    # 1. Surah catalog (static, 114 rows).
    surahs = await surah_repo.list_all(db)

    # 2. Active (or all) students in the school, filtered by class if given.
    student_stmt = select(Student).where(Student.school_id == school_id)
    if not include_archived:
        student_stmt = student_stmt.where(Student.status != StudentStatus.ARCHIVED)
    if class_id is not None:
        student_stmt = student_stmt.where(Student.class_id == class_id)
    student_stmt = student_stmt.order_by(Student.full_name)
    students = list((await db.execute(student_stmt)).scalars().all())

    if not students:
        return MatrixView(
            surahs=[SurahRead.model_validate(s) for s in surahs],
            students=[],
        )

    student_ids = [s.id for s in students]

    # 3. One query for ALL progress rows belonging to those students.
    progress_stmt = select(
        MemorizationProgress.student_id,
        MemorizationProgress.surah_id,
        MemorizationProgress.status,
        MemorizationProgress.completion_percent,
    ).where(MemorizationProgress.student_id.in_(student_ids))

    progress_by_student: dict[UUID, list[MatrixCell]] = {sid: [] for sid in student_ids}
    for sid, surah_id, status, percent in (await db.execute(progress_stmt)).all():
        progress_by_student[sid].append(
            MatrixCell(
                surah_id=surah_id,
                status=status,
                completion_percent=int(percent),
            )
        )

    return MatrixView(
        surahs=[SurahRead.model_validate(s) for s in surahs],
        students=[
            MatrixStudent(
                id=s.id,
                full_name=s.full_name,
                class_id=s.class_id,
                cells=progress_by_student.get(s.id, []),
            )
            for s in students
        ],
    )
