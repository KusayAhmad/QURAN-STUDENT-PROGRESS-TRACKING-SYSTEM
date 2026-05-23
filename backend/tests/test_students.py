"""Student CRUD + tenant isolation."""
import pytest

pytestmark = pytest.mark.asyncio


async def test_create_and_list_student(auth_client):
    create = await auth_client.post(
        "/api/v1/students",
        json={"full_name": "Ahmad Ali", "gender": "MALE"},
    )
    assert create.status_code == 201, create.text
    student = create.json()
    assert student["full_name"] == "Ahmad Ali"
    assert student["status"] == "ACTIVE"

    lst = await auth_client.get("/api/v1/students")
    assert lst.status_code == 200
    body = lst.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == student["id"]


async def test_get_update_archive(auth_client):
    created = (
        await auth_client.post(
            "/api/v1/students",
            json={"full_name": "Maryam Hassan", "gender": "FEMALE"},
        )
    ).json()
    sid = created["id"]

    got = await auth_client.get(f"/api/v1/students/{sid}")
    assert got.status_code == 200

    upd = await auth_client.put(
        f"/api/v1/students/{sid}", json={"guardian_name": "Hassan", "notes": "Strong"}
    )
    assert upd.status_code == 200
    assert upd.json()["guardian_name"] == "Hassan"

    arch = await auth_client.delete(f"/api/v1/students/{sid}")
    assert arch.status_code == 200
    assert arch.json()["status"] == "ARCHIVED"

    # Default list excludes archived
    lst = await auth_client.get("/api/v1/students")
    assert lst.json()["total"] == 0
    # But include_archived returns it
    lst2 = await auth_client.get("/api/v1/students?include_archived=true")
    assert lst2.json()["total"] == 1


async def test_search_filter(auth_client):
    for name in ["Yusuf", "Yasin", "Khadijah"]:
        await auth_client.post(
            "/api/v1/students", json={"full_name": name, "gender": "MALE"}
        )
    res = await auth_client.get("/api/v1/students?search=Y")
    assert res.json()["total"] == 2


async def test_unauthenticated_blocked(client):
    res = await client.get("/api/v1/students")
    assert res.status_code == 401
