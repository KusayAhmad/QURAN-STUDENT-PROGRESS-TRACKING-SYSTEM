"""Admin user create/update."""
import pytest

pytestmark = pytest.mark.asyncio

# Reuse the admin_client fixture
pytest_plugins = ["tests.test_audit_log"]


async def test_admin_creates_teacher(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/users",
        json={
            "name": "New Teacher",
            "email": "newteacher@example.com",
            "password": "StrongPass123",
            "role": "TEACHER",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["email"] == "newteacher@example.com"
    assert body["role"] == "TEACHER"
    assert body["is_active"] is True
    # password_hash MUST NOT leak
    assert "password" not in body
    assert "password_hash" not in body


async def test_create_user_duplicate_email_409(admin_client):
    # admin@example.com is already created by the admin_client fixture
    res = await admin_client.post(
        "/api/v1/admin/users",
        json={
            "name": "Dup",
            "email": "admin@example.com",
            "password": "StrongPass123",
        },
    )
    assert res.status_code == 409


async def test_create_user_validation(admin_client):
    res = await admin_client.post(
        "/api/v1/admin/users",
        json={"name": "X", "email": "invalid-email", "password": "short"},
    )
    assert res.status_code == 422


async def test_create_user_admin_only(auth_client):
    """A teacher must NOT be able to create users."""
    res = await auth_client.post(
        "/api/v1/admin/users",
        json={
            "name": "X",
            "email": "x@example.com",
            "password": "StrongPass123",
        },
    )
    assert res.status_code == 403


async def test_admin_can_login_as_new_teacher(admin_client, client):
    """End-to-end: create a teacher, then log in as them."""
    await admin_client.post(
        "/api/v1/admin/users",
        json={
            "name": "Roster Teacher",
            "email": "roster@example.com",
            "password": "MyPassword456",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "roster@example.com", "password": "MyPassword456"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


async def test_admin_can_update_user(admin_client):
    created = (
        await admin_client.post(
            "/api/v1/admin/users",
            json={
                "name": "Mutable",
                "email": "mutable@example.com",
                "password": "StrongPass123",
            },
        )
    ).json()

    upd = await admin_client.put(
        f"/api/v1/admin/users/{created['id']}",
        json={"name": "Renamed", "is_active": False},
    )
    assert upd.status_code == 200
    body = upd.json()
    assert body["name"] == "Renamed"
    assert body["is_active"] is False


async def test_admin_cannot_demote_self(admin_client):
    """Self-protection: admins cannot change their own role to TEACHER."""
    me = (await admin_client.get("/api/v1/auth/me")).json()
    res = await admin_client.put(
        f"/api/v1/admin/users/{me['id']}", json={"role": "TEACHER"}
    )
    assert res.status_code == 400


async def test_admin_cannot_deactivate_self(admin_client):
    me = (await admin_client.get("/api/v1/auth/me")).json()
    res = await admin_client.put(
        f"/api/v1/admin/users/{me['id']}", json={"is_active": False}
    )
    assert res.status_code == 400


async def test_password_change_takes_effect(admin_client, client):
    created = (
        await admin_client.post(
            "/api/v1/admin/users",
            json={
                "name": "PwReset",
                "email": "pwreset@example.com",
                "password": "OldPassword123",
            },
        )
    ).json()
    # Update with new password
    await admin_client.put(
        f"/api/v1/admin/users/{created['id']}", json={"password": "NewPassword456"}
    )
    # Old password should fail
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "pwreset@example.com", "password": "OldPassword123"},
    )
    assert bad.status_code == 401
    # New password should work
    good = await client.post(
        "/api/v1/auth/login",
        json={"email": "pwreset@example.com", "password": "NewPassword456"},
    )
    assert good.status_code == 200


async def test_update_user_cross_tenant_blocked(
    admin_client, second_school_teacher
):
    """An admin from school A cannot update a user from school B."""
    me_b = (await second_school_teacher.get("/api/v1/auth/me")).json()
    res = await admin_client.put(
        f"/api/v1/admin/users/{me_b['id']}", json={"name": "hacked"}
    )
    assert res.status_code == 404


async def test_user_create_recorded_in_audit_log(admin_client):
    created = (
        await admin_client.post(
            "/api/v1/admin/users",
            json={
                "name": "Audited",
                "email": "audited@example.com",
                "password": "StrongPass123",
            },
        )
    ).json()
    res = await admin_client.get(
        f"/api/v1/admin/audit-logs?entity_type=USER&entity_id={created['id']}"
    )
    body = res.json()
    create_log = next(item for item in body["items"] if item["action"] == "CREATE")
    assert create_log["new_value"]["email"] == "audited@example.com"
    # Password hash MUST NOT be in the audit value
    assert "password_hash" not in create_log["new_value"]
    assert "password" not in create_log["new_value"]
