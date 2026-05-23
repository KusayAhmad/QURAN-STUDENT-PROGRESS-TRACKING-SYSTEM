"""Per-surah progress timeline (blueprint §12-A)."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client) -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Bilal", "gender": "MALE"}
        )
    ).json()["id"]


async def test_timeline_records_each_status_change(auth_client, seeded_surahs):
    """Baqarah: WEAK -> REVIEW_REQUIRED -> STRONG -> MASTERED."""
    sid = await _create_student(auth_client)

    sequence = ["WEAK", "REVIEW_REQUIRED", "STRONG", "MASTERED"]
    for idx, st in enumerate(sequence):
        res = await auth_client.post(
            f"/api/v1/students/{sid}/progress",
            json={"surah_id": 2, "status": st, "completion_percent": 25 * (idx + 1)},
        )
        assert res.status_code == 200, res.text

    timeline = await auth_client.get(
        f"/api/v1/students/{sid}/surahs/2/timeline"
    )
    assert timeline.status_code == 200
    body = timeline.json()
    assert len(body) == 4
    assert [p["status"] for p in body] == sequence
    assert [p["action"] for p in body] == ["CREATE", "UPDATE", "UPDATE", "UPDATE"]
    # Snapshots monotonically capture completion_percent
    assert body[0]["completion_percent"] == 25
    assert body[-1]["completion_percent"] == 100


async def test_timeline_isolated_per_surah(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 2, "status": "WEAK", "completion_percent": 20},
    )

    s1 = (await auth_client.get(f"/api/v1/students/{sid}/surahs/1/timeline")).json()
    s2 = (await auth_client.get(f"/api/v1/students/{sid}/surahs/2/timeline")).json()
    assert len(s1) == 1 and s1[0]["status"] == "STRONG"
    assert len(s2) == 1 and s2[0]["status"] == "WEAK"


async def test_timeline_empty_for_untouched_surah(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.get(f"/api/v1/students/{sid}/surahs/1/timeline")
    assert res.status_code == 200
    assert res.json() == []


async def test_timeline_unknown_student(auth_client, seeded_surahs):
    res = await auth_client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/surahs/1/timeline"
    )
    assert res.status_code == 404


async def test_timeline_cross_tenant_blocked(
    auth_client, seeded_surahs, second_school_teacher
):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Khalid (A)", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )
    res = await second_school_teacher.get(f"/api/v1/students/{sid}/surahs/1/timeline")
    assert res.status_code == 404
