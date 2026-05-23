"""Evaluation routes."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client) -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Bilal", "gender": "MALE"}
        )
    ).json()["id"]


async def test_create_and_list_evaluation(auth_client):
    sid = await _create_student(auth_client)

    create = await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={
            "type": "ORAL_RECITATION",
            "exam_date": "2026-05-10",
            "tajweed_score": 90,
            "accuracy_score": 85,
            "fluency_score": 88,
            "retention_score": 80,
            "speed_score": 75,
            "confidence_score": 92,
            "notes": "Strong recitation, slight pacing issues.",
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    # Auto-computed overall = mean of 6 axes = round(510/6) = 85
    assert body["overall_score"] == 85
    assert body["type"] == "ORAL_RECITATION"

    listing = await auth_client.get(f"/api/v1/students/{sid}/evaluations")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


async def test_explicit_overall_score_not_overwritten(auth_client):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={
            "type": "MONTHLY_REVIEW",
            "exam_date": "2026-05-12",
            "tajweed_score": 50,
            "overall_score": 95,
        },
    )
    assert res.status_code == 201
    assert res.json()["overall_score"] == 95


async def test_evaluation_score_validation(auth_client):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={
            "type": "ACCURACY_TEST",
            "exam_date": "2026-05-12",
            "tajweed_score": 150,
        },
    )
    assert res.status_code == 422


async def test_evaluation_unknown_student(auth_client):
    res = await auth_client.post(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/evaluations",
        json={"type": "OTHER", "exam_date": "2026-05-12"},
    )
    assert res.status_code == 404


async def test_get_and_delete_evaluation(auth_client):
    sid = await _create_student(auth_client)
    created = (
        await auth_client.post(
            f"/api/v1/students/{sid}/evaluations",
            json={"type": "OTHER", "exam_date": "2026-05-12", "overall_score": 70},
        )
    ).json()
    eid = created["id"]

    got = await auth_client.get(f"/api/v1/evaluations/{eid}")
    assert got.status_code == 200
    assert got.json()["overall_score"] == 70

    rem = await auth_client.delete(f"/api/v1/evaluations/{eid}")
    assert rem.status_code == 204

    again = await auth_client.get(f"/api/v1/evaluations/{eid}")
    assert again.status_code == 404
