"""Observation routes."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client) -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Aisha", "gender": "FEMALE"}
        )
    ).json()["id"]


async def test_create_list_delete_observation(auth_client):
    sid = await _create_student(auth_client)

    create = await auth_client.post(
        f"/api/v1/students/{sid}/observations",
        json={"type": "WEAK_PRONUNCIATION", "message": "Letter qaf needs work"},
    )
    assert create.status_code == 201
    oid = create.json()["id"]

    listing = await auth_client.get(f"/api/v1/students/{sid}/observations")
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    assert body["items"][0]["message"] == "Letter qaf needs work"

    rem = await auth_client.delete(f"/api/v1/observations/{oid}")
    assert rem.status_code == 204

    after = await auth_client.get(f"/api/v1/students/{sid}/observations")
    assert after.json()["total"] == 0


async def test_observation_default_type(auth_client):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/observations",
        json={"message": "Behaved well today."},
    )
    assert res.status_code == 201
    assert res.json()["type"] == "GENERAL"


async def test_observation_unknown_student(auth_client):
    res = await auth_client.post(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/observations",
        json={"message": "x"},
    )
    assert res.status_code == 404


async def test_observation_empty_message_rejected(auth_client):
    sid = await _create_student(auth_client)
    res = await auth_client.post(
        f"/api/v1/students/{sid}/observations", json={"message": ""}
    )
    assert res.status_code == 422
