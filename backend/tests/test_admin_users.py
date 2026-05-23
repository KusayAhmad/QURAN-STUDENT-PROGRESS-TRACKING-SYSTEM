"""Admin user list endpoint."""
import pytest

pytestmark = pytest.mark.asyncio

# Reuse the admin_client fixture
pytest_plugins = ["tests.test_audit_log"]


async def test_admin_can_list_school_users(admin_client):
    res = await admin_client.get("/api/v1/admin/users")
    assert res.status_code == 200
    emails = [u["email"] for u in res.json()]
    assert "admin@example.com" in emails
    assert "teacher@example.com" in emails


async def test_teachers_blocked(auth_client):
    res = await auth_client.get("/api/v1/admin/users")
    assert res.status_code == 403


async def test_user_list_tenant_scoped(admin_client, second_school_teacher):
    """The admin's school listing should not include the second-school teacher."""
    res = await admin_client.get("/api/v1/admin/users")
    emails = [u["email"] for u in res.json()]
    assert "other-teacher@example.com" not in emails
