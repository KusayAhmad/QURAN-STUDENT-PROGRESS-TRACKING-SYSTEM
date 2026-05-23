"""Audit log: assert mutations are recorded; reads are admin-only and tenant-scoped."""
import pytest
import pytest_asyncio

from app.core.security import hash_password
from app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def admin_client(client, session_factory, seed_school_and_teacher):
    """An admin in the SAME school as the default teacher fixture."""
    school, _, _ = seed_school_and_teacher
    async with session_factory() as db:
        admin = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hash_password("admin-pass-789"),
            role=UserRole.ADMIN,
            school_id=school.id,
        )
        db.add(admin)
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin-pass-789"},
    )
    assert login.status_code == 200, login.text

    class AdminWrapper:
        def __init__(self, c, token):
            self._c = c
            self._h = {"Authorization": f"Bearer {token}"}

        async def get(self, url, **kw):
            kw.setdefault("headers", {}).update(self._h)
            return await self._c.get(url, **kw)

        async def post(self, url, **kw):
            kw.setdefault("headers", {}).update(self._h)
            return await self._c.post(url, **kw)

        async def put(self, url, **kw):
            kw.setdefault("headers", {}).update(self._h)
            return await self._c.put(url, **kw)

        async def delete(self, url, **kw):
            kw.setdefault("headers", {}).update(self._h)
            return await self._c.delete(url, **kw)

    return AdminWrapper(client, login.json()["access_token"])


async def test_student_create_recorded(auth_client, admin_client):
    created = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Logged Student", "gender": "MALE"}
        )
    ).json()

    res = await admin_client.get("/api/v1/admin/audit-logs?entity_type=STUDENT")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] >= 1
    log = body["items"][0]  # most recent first
    assert log["action"] == "CREATE"
    assert log["entity_id"] == created["id"]
    assert log["new_value"]["full_name"] == "Logged Student"
    assert log["old_value"] is None


async def test_student_archive_recorded(auth_client, admin_client):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Soon Archived", "gender": "FEMALE"}
        )
    ).json()["id"]
    await auth_client.delete(f"/api/v1/students/{sid}")

    res = await admin_client.get(
        f"/api/v1/admin/audit-logs?entity_type=STUDENT&entity_id={sid}"
    )
    body = res.json()
    actions = [item["action"] for item in body["items"]]
    assert "ARCHIVE" in actions
    assert "CREATE" in actions


async def test_progress_update_records_old_and_new(
    auth_client, admin_client, seeded_surahs
):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Diff Test", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "WEAK", "completion_percent": 20},
    )
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )

    res = await admin_client.get("/api/v1/admin/audit-logs?entity_type=PROGRESS")
    body = res.json()
    update_log = next(item for item in body["items"] if item["action"] == "UPDATE")
    assert update_log["old_value"]["status"] == "WEAK"
    assert update_log["new_value"]["status"] == "MASTERED"
    assert update_log["old_value"]["completion_percent"] == 20
    assert update_log["new_value"]["completion_percent"] == 100


async def test_audit_logs_admin_only(auth_client):
    """A teacher (not admin) must NOT be able to read audit logs."""
    res = await auth_client.get("/api/v1/admin/audit-logs")
    assert res.status_code == 403


async def test_audit_logs_tenant_scoped(
    auth_client, admin_client, second_school_teacher
):
    """School A's admin must not see school B's actions, and vice versa.

    We let the second-school teacher mutate; admin (school A) should NOT see it.
    """
    await second_school_teacher.post(
        "/api/v1/students",
        json={"full_name": "School B Student", "gender": "MALE"},
    )
    res = await admin_client.get("/api/v1/admin/audit-logs?entity_type=STUDENT")
    body = res.json()
    for item in body["items"]:
        assert item["new_value"]["full_name"] != "School B Student"
