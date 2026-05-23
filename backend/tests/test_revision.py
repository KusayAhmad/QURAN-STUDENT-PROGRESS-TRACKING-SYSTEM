"""Smart revision suggestions (blueprint §12-C).

Covers:
  - empty state (no progress rows)
  - WEAK + REVIEW_REQUIRED ranked highest
  - STALE_MASTERED / STALE_STRONG: thresholds applied
  - NOT_STARTED / fresh-MASTERED filtered out
  - tenant isolation
  - limit param honored
"""
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client, name: str = "Bilal") -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": name, "gender": "MALE"}
        )
    ).json()["id"]


async def _set_progress(auth_client, sid: str, **payload):
    payload.setdefault("completion_percent", 50)
    return await auth_client.post(
        f"/api/v1/students/{sid}/progress", json=payload
    )


async def test_revision_suggestions_no_progress(auth_client, seeded_surahs):
    """A student with no recorded progress yields an empty list."""
    sid = await _create_student(auth_client)
    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    assert res.status_code == 200
    body = res.json()
    assert body["student_id"] == sid
    assert body["suggestions"] == []


async def test_revision_suggestions_unknown_student(auth_client, seeded_surahs):
    res = await auth_client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/revision-suggestions"
    )
    assert res.status_code == 404


async def test_revision_weak_ranks_above_review_required(
    auth_client, seeded_surahs
):
    """WEAK should appear before REVIEW_REQUIRED in the ranked list."""
    sid = await _create_student(auth_client)
    # Surah 1 = REVIEW_REQUIRED, surah 2 = WEAK
    await _set_progress(
        auth_client, sid, surah_id=1, status="REVIEW_REQUIRED", completion_percent=70
    )
    await _set_progress(
        auth_client, sid, surah_id=2, status="WEAK", completion_percent=30
    )

    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    assert res.status_code == 200
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 2
    assert suggestions[0]["surah_id"] == 2
    assert suggestions[0]["reason"] == "WEAK"
    assert suggestions[0]["surah_name_en"] == "Al-Baqarah"
    assert suggestions[1]["reason"] == "REVIEW_REQUIRED"
    # Priority scores should be strictly ordered
    assert suggestions[0]["priority_score"] > suggestions[1]["priority_score"]


async def test_revision_filters_not_started_and_fresh_mastered(
    auth_client, seeded_surahs
):
    """NOT_STARTED and recently-reviewed MASTERED rows should be excluded."""
    sid = await _create_student(auth_client)
    await _set_progress(
        auth_client, sid, surah_id=1, status="NOT_STARTED", completion_percent=0
    )
    # Mastered AND reviewed today -> should NOT be suggested
    today_iso = datetime.now(timezone.utc).isoformat()
    await _set_progress(
        auth_client,
        sid,
        surah_id=2,
        status="MASTERED",
        completion_percent=100,
        last_reviewed_at=today_iso,
    )

    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    assert res.json()["suggestions"] == []


async def test_revision_surfaces_stale_mastered(
    auth_client, seeded_surahs, session_factory
):
    """A MASTERED surah unreviewed for >30 days should surface as STALE_MASTERED."""
    sid = await _create_student(auth_client)
    # First record progress through the API to get the row id
    await _set_progress(
        auth_client, sid, surah_id=1, status="MASTERED", completion_percent=100
    )

    # Then back-date last_reviewed_at directly in the DB (the API doesn't let
    # you set arbitrary historical dates, so we go around it for the test).
    from uuid import UUID

    from sqlalchemy import select

    from app.models.memorization_progress import MemorizationProgress

    async with session_factory() as db:
        row = (
            await db.execute(
                select(MemorizationProgress).where(
                    MemorizationProgress.student_id == UUID(sid),
                    MemorizationProgress.surah_id == 1,
                )
            )
        ).scalar_one()
        row.last_reviewed_at = datetime.now(timezone.utc) - timedelta(days=45)
        await db.commit()

    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["surah_id"] == 1
    assert suggestions[0]["reason"] == "STALE_MASTERED"
    assert suggestions[0]["days_since_review"] >= 45


async def test_revision_surfaces_stale_strong(
    auth_client, seeded_surahs, session_factory
):
    """A STRONG surah unreviewed for >14 days should surface as STALE_STRONG."""
    sid = await _create_student(auth_client)
    await _set_progress(
        auth_client, sid, surah_id=1, status="STRONG", completion_percent=80
    )

    from uuid import UUID

    from sqlalchemy import select

    from app.models.memorization_progress import MemorizationProgress

    async with session_factory() as db:
        row = (
            await db.execute(
                select(MemorizationProgress).where(
                    MemorizationProgress.student_id == UUID(sid),
                    MemorizationProgress.surah_id == 1,
                )
            )
        ).scalar_one()
        row.last_reviewed_at = datetime.now(timezone.utc) - timedelta(days=20)
        await db.commit()

    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["reason"] == "STALE_STRONG"


async def test_revision_in_progress_low_completion_excluded(
    auth_client, seeded_surahs
):
    """IN_PROGRESS rows below 10% completion are noise and should be excluded."""
    sid = await _create_student(auth_client)
    await _set_progress(
        auth_client, sid, surah_id=1, status="IN_PROGRESS", completion_percent=5
    )
    await _set_progress(
        auth_client, sid, surah_id=2, status="IN_PROGRESS", completion_percent=60
    )

    res = await auth_client.get(f"/api/v1/students/{sid}/revision-suggestions")
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["surah_id"] == 2
    assert suggestions[0]["reason"] == "IN_PROGRESS"


async def test_revision_limit_param(auth_client, seeded_surahs):
    """The limit query param caps the response length."""
    sid = await _create_student(auth_client)
    await _set_progress(
        auth_client, sid, surah_id=1, status="WEAK", completion_percent=20
    )
    await _set_progress(
        auth_client, sid, surah_id=2, status="REVIEW_REQUIRED", completion_percent=50
    )

    res = await auth_client.get(
        f"/api/v1/students/{sid}/revision-suggestions?limit=1"
    )
    assert res.status_code == 200
    suggestions = res.json()["suggestions"]
    assert len(suggestions) == 1
    # WEAK outranks REVIEW_REQUIRED
    assert suggestions[0]["reason"] == "WEAK"


async def test_revision_limit_param_validation(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.get(
        f"/api/v1/students/{sid}/revision-suggestions?limit=0"
    )
    assert res.status_code == 422

    res = await auth_client.get(
        f"/api/v1/students/{sid}/revision-suggestions?limit=999"
    )
    assert res.status_code == 422


async def test_revision_tenant_isolation(
    auth_client, second_school_teacher, seeded_surahs
):
    """A teacher from another school cannot fetch suggestions for our student."""
    sid = await _create_student(auth_client)
    await _set_progress(
        auth_client, sid, surah_id=1, status="WEAK", completion_percent=10
    )

    res = await second_school_teacher.get(
        f"/api/v1/students/{sid}/revision-suggestions"
    )
    assert res.status_code == 404
