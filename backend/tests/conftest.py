"""Test fixtures: in-memory SQLite + override DB dependency + auth helper."""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# Override settings BEFORE importing app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-only-for-tests-do-not-use")
os.environ.setdefault("DEBUG", "false")

# Disable rate limiting for tests
from app.core.rate_limit import disable_rate_limiting
disable_rate_limiting()

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.school import School
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator:
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_school_and_teacher(session_factory):
    """Create a school + a teacher user. Returns (school, teacher, plain_password)."""
    async with session_factory() as db:
        school = School(name="Test School", timezone="UTC")
        db.add(school)
        await db.flush()
        teacher = User(
            name="Test Teacher",
            email="teacher@example.com",
            password_hash=hash_password("test-pass-123"),
            role=UserRole.TEACHER,
            school_id=school.id,
        )
        db.add(teacher)
        await db.commit()
        await db.refresh(school)
        await db.refresh(teacher)
        return school, teacher, "test-pass-123"


@pytest_asyncio.fixture
async def auth_client(client, seed_school_and_teacher):
    """Authenticated client (teacher token in Authorization header)."""
    _, teacher, password = seed_school_and_teacher
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": teacher.email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def seeded_surahs(session_factory):
    """Insert a couple of surahs for tests that need them."""
    from app.models.surah import QuranSurah

    async with session_factory() as db:
        db.add_all(
            [
                QuranSurah(
                    id=1,
                    surah_order=1,
                    surah_name_ar="الفاتحة",
                    surah_name_en="Al-Fatihah",
                    ayah_count=7,
                    juz_no=1,
                    hizb_no=1,
                ),
                QuranSurah(
                    id=2,
                    surah_order=2,
                    surah_name_ar="البقرة",
                    surah_name_en="Al-Baqarah",
                    ayah_count=286,
                    juz_no=1,
                    hizb_no=1,
                ),
            ]
        )
        await db.commit()


@pytest.fixture(autouse=True)
def _ensure_anyio_backend():
    """pytest-asyncio in auto mode handles loops; this is a placeholder hook."""
    return None



@pytest_asyncio.fixture
async def second_school_teacher(client, session_factory):
    """Create a SECOND school + teacher and return an authenticated httpx client.

    Useful for asserting cross-tenant isolation: students/evaluations/etc.
    created by School A must be invisible to School B.
    """
    async with session_factory() as db:
        other_school = School(name="Other School", timezone="UTC")
        db.add(other_school)
        await db.flush()
        other_teacher = User(
            name="Other Teacher",
            email="other-teacher@example.com",
            password_hash=hash_password("other-pass-456"),
            role=UserRole.TEACHER,
            school_id=other_school.id,
        )
        db.add(other_teacher)
        await db.commit()
        await db.refresh(other_school)
        await db.refresh(other_teacher)

    # Login as the other teacher on a fresh client header. We reuse the same
    # AsyncClient so it shares the dependency override; just override the
    # Authorization header for the duration of this fixture.
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "other-teacher@example.com", "password": "other-pass-456"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    class OtherClient:
        """Wraps the shared httpx client so this fixture does not stomp on the
        primary `auth_client`'s Authorization header."""

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

    return OtherClient(client, token)
