"""Auth flow: login, refresh, /me, bad creds, expired/invalid tokens."""
import pytest


pytestmark = pytest.mark.asyncio


async def test_login_success(client, seed_school_and_teacher):
    _, teacher, password = seed_school_and_teacher
    resp = await client.post(
        "/api/v1/auth/login", json={"email": teacher.email, "password": password}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client, seed_school_and_teacher):
    _, teacher, _ = seed_school_and_teacher
    resp = await client.post(
        "/api/v1/auth/login", json={"email": teacher.email, "password": "WRONG"}
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@x.com", "password": "x"}
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_user(auth_client, seed_school_and_teacher):
    _, teacher, _ = seed_school_and_teacher
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == teacher.email
    assert body["role"] == "TEACHER"


async def test_refresh_flow(client, seed_school_and_teacher):
    _, teacher, password = seed_school_and_teacher
    login = await client.post(
        "/api/v1/auth/login", json={"email": teacher.email, "password": password}
    )
    refresh_token = login.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_with_access_token_rejected(client, seed_school_and_teacher):
    _, teacher, password = seed_school_and_teacher
    login = await client.post(
        "/api/v1/auth/login", json={"email": teacher.email, "password": password}
    )
    access_token = login.json()["access_token"]
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert resp.status_code == 401
