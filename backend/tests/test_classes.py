"""Class CRUD: reads = any school user, writes = ADMIN."""
import pytest

pytestmark = pytest.mark.asyncio


# Reuse the admin_client fixture from test_audit_log.py
pytest_plugins = ["tests.test_audit_log"]


async def test_create_requires_admin(auth_client):
    """Teachers (non-admin) must NOT be able to create classes."""
    res = await auth_client.post(
        "/api/v1/classes", json={"name": "Section A", "academic_year": "2025-2026"}
    )
    assert res.status_code == 403


async def test_admin_can_create_list_get(admin_client):
    create = await admin_client.post(
        "/api/v1/classes", json={"name": "Section A", "academic_year": "2025-2026"}
    )
    assert create.status_code == 201, create.text
    cid = create.json()["id"]

    listing = await admin_client.get("/api/v1/classes")
    assert listing.status_code == 200
    assert any(c["id"] == cid for c in listing.json())

    one = await admin_client.get(f"/api/v1/classes/{cid}")
    assert one.status_code == 200
    assert one.json()["name"] == "Section A"


async def test_teacher_can_read_classes(auth_client, admin_client):
    created = (
        await admin_client.post(
            "/api/v1/classes", json={"name": "Section B", "academic_year": "2025-2026"}
        )
    ).json()
    res = await auth_client.get(f"/api/v1/classes/{created['id']}")
    assert res.status_code == 200


async def test_admin_can_update_and_delete(admin_client):
    cid = (
        await admin_client.post(
            "/api/v1/classes", json={"name": "Section C", "academic_year": "2025-2026"}
        )
    ).json()["id"]

    upd = await admin_client.put(
        f"/api/v1/classes/{cid}", json={"name": "Section C - Renamed"}
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Section C - Renamed"

    rem = await admin_client.delete(f"/api/v1/classes/{cid}")
    assert rem.status_code == 204

    after = await admin_client.get(f"/api/v1/classes/{cid}")
    assert after.status_code == 404


async def test_class_cross_tenant_blocked(admin_client, second_school_teacher):
    """A class created by School A admin is invisible to School B teacher."""
    cid = (
        await admin_client.post(
            "/api/v1/classes", json={"name": "Section A", "academic_year": "2025-2026"}
        )
    ).json()["id"]
    res = await second_school_teacher.get(f"/api/v1/classes/{cid}")
    assert res.status_code == 404
