"""Memorization progress: upsert, list, validation, surah lookup."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client) -> str:
    resp = await auth_client.post(
        "/api/v1/students", json={"full_name": "Bilal", "gender": "MALE"}
    )
    return resp.json()["id"]


async def test_list_surahs(auth_client, seeded_surahs):
    res = await auth_client.get("/api/v1/surahs")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2
    assert body[0]["surah_name_en"] == "Al-Fatihah"


async def test_upsert_progress_creates_then_updates(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)

    create = await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={
            "surah_id": 1,
            "status": "MASTERED",
            "score": 95,
            "completion_percent": 100,
            "notes": "Excellent recitation",
        },
    )
    assert create.status_code == 200, create.text
    p1 = create.json()
    assert p1["status"] == "MASTERED"
    assert p1["score"] == 95

    # Same (student, surah) -> upsert, NOT a duplicate
    update = await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={
            "surah_id": 1,
            "status": "REVIEW_REQUIRED",
            "score": 70,
            "completion_percent": 100,
            "notes": "Needs review",
        },
    )
    assert update.status_code == 200
    p2 = update.json()
    assert p2["id"] == p1["id"]  # same row
    assert p2["status"] == "REVIEW_REQUIRED"

    listing = await auth_client.get(f"/api/v1/students/{sid}/progress")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_progress_invalid_score_rejected(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "score": 150, "completion_percent": 50},
    )
    assert res.status_code == 422


async def test_progress_unknown_surah(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 999, "status": "STRONG", "completion_percent": 0},
    )
    assert res.status_code == 404


async def test_progress_unknown_student(auth_client, seeded_surahs):
    res = await auth_client.post(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 0},
    )
    assert res.status_code == 404


async def test_progress_partial_update(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    created = (
        await auth_client.post(
            f"/api/v1/students/{sid}/progress",
            json={"surah_id": 2, "status": "WEAK", "completion_percent": 30},
        )
    ).json()

    upd = await auth_client.put(
        f"/api/v1/progress/{created['id']}",
        json={"status": "STRONG", "score": 88},
    )
    assert upd.status_code == 200
    body = upd.json()
    assert body["status"] == "STRONG"
    assert body["score"] == 88
    assert body["completion_percent"] == 30  # unchanged
