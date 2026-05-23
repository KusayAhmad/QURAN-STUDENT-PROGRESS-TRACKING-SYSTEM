"""Cross-tenant isolation: school B must not see / mutate school A's data."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_student_invisible_to_other_tenant(auth_client, second_school_teacher):
    created = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Khalid (school A)", "gender": "MALE"}
        )
    ).json()
    sid = created["id"]

    # School B teacher should NOT see this student
    res = await second_school_teacher.get(f"/api/v1/students/{sid}")
    assert res.status_code == 404

    listing = await second_school_teacher.get("/api/v1/students")
    assert listing.json()["total"] == 0


async def test_student_not_archivable_by_other_tenant(auth_client, second_school_teacher):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Mariam (A)", "gender": "FEMALE"}
        )
    ).json()["id"]

    # Cross-tenant archive must 404, not silently succeed
    res = await second_school_teacher.delete(f"/api/v1/students/{sid}")
    assert res.status_code == 404

    # Verify School A still sees the student as ACTIVE
    still_there = await auth_client.get(f"/api/v1/students/{sid}")
    assert still_there.status_code == 200
    assert still_there.json()["status"] == "ACTIVE"


async def test_progress_invisible_to_other_tenant(
    auth_client, seeded_surahs, second_school_teacher
):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Omar (A)", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )

    # Listing the student's progress as school B must 404
    res = await second_school_teacher.get(f"/api/v1/students/{sid}/progress")
    assert res.status_code == 404


async def test_evaluation_invisible_to_other_tenant(auth_client, second_school_teacher):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Hamza (A)", "gender": "MALE"}
        )
    ).json()["id"]
    eid = (
        await auth_client.post(
            f"/api/v1/students/{sid}/evaluations",
            json={"type": "OTHER", "exam_date": "2026-05-10", "overall_score": 80},
        )
    ).json()["id"]

    # Cross-tenant fetch must 404
    res = await second_school_teacher.get(f"/api/v1/evaluations/{eid}")
    assert res.status_code == 404

    # Cross-tenant update must 404
    res = await second_school_teacher.put(
        f"/api/v1/evaluations/{eid}", json={"overall_score": 1}
    )
    assert res.status_code == 404

    # Cross-tenant delete must 404
    res = await second_school_teacher.delete(f"/api/v1/evaluations/{eid}")
    assert res.status_code == 404


async def test_analytics_scoped_to_caller_school(
    auth_client, seeded_surahs, second_school_teacher
):
    # School A: 1 student with 1 mastered surah
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Ali (A)", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )

    a_view = (await auth_client.get("/api/v1/analytics/school")).json()
    b_view = (await second_school_teacher.get("/api/v1/analytics/school")).json()

    assert a_view["student_count"] == 1
    assert a_view["counts_by_status"]["MASTERED"] == 1

    assert b_view["student_count"] == 0
    assert b_view["counts_by_status"]["MASTERED"] == 0
    assert a_view["school_id"] != b_view["school_id"]
