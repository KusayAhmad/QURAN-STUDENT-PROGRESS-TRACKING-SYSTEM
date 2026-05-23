"""Bulk Quran×Student matrix view."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client, name: str) -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": name, "gender": "MALE"}
        )
    ).json()["id"]


async def test_matrix_empty_when_no_students(auth_client, seeded_surahs):
    res = await auth_client.get("/api/v1/students/matrix")
    assert res.status_code == 200
    body = res.json()
    assert len(body["surahs"]) == 2  # the test fixture seeds only 2 surahs
    assert body["students"] == []


async def test_matrix_returns_progress_per_student(auth_client, seeded_surahs):
    s1 = await _create_student(auth_client, "Ali")
    s2 = await _create_student(auth_client, "Bilal")

    await auth_client.post(
        f"/api/v1/students/{s1}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )
    await auth_client.post(
        f"/api/v1/students/{s1}/progress",
        json={"surah_id": 2, "status": "WEAK", "completion_percent": 30},
    )
    await auth_client.post(
        f"/api/v1/students/{s2}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )

    res = await auth_client.get("/api/v1/students/matrix")
    assert res.status_code == 200
    body = res.json()
    assert len(body["students"]) == 2

    # Sorted alphabetically by full_name -> Ali, Bilal
    by_name = {s["full_name"]: s for s in body["students"]}
    ali_cells = {c["surah_id"]: c for c in by_name["Ali"]["cells"]}
    bilal_cells = {c["surah_id"]: c for c in by_name["Bilal"]["cells"]}

    assert ali_cells[1]["status"] == "MASTERED"
    assert ali_cells[2]["status"] == "WEAK"
    assert bilal_cells[1]["status"] == "STRONG"
    assert 2 not in bilal_cells  # no row for surah 2


async def test_matrix_excludes_archived_by_default(auth_client, seeded_surahs):
    sid = await _create_student(auth_client, "Soon-Archived")
    await auth_client.delete(f"/api/v1/students/{sid}")
    res = await auth_client.get("/api/v1/students/matrix")
    body = res.json()
    assert all(s["id"] != sid for s in body["students"])

    # include_archived=true should bring them back
    res2 = await auth_client.get("/api/v1/students/matrix?include_archived=true")
    body2 = res2.json()
    assert any(s["id"] == sid for s in body2["students"])


async def test_matrix_filters_by_class(auth_client, session_factory, seeded_surahs):
    from app.models.class_ import Class

    me = (await auth_client.get("/api/v1/auth/me")).json()
    async with session_factory() as db:
        klass = Class(school_id=me["school_id"], name="Section A", academic_year="2025-2026")
        db.add(klass)
        await db.commit()
        await db.refresh(klass)
        cid = str(klass.id)

    in_class = await _create_student(auth_client, "InClass")
    not_in_class = await _create_student(auth_client, "NotInClass")
    await auth_client.put(f"/api/v1/students/{in_class}", json={"class_id": cid})

    res = await auth_client.get(f"/api/v1/students/matrix?class_id={cid}")
    body = res.json()
    ids = [s["id"] for s in body["students"]]
    assert in_class in ids
    assert not_in_class not in ids


async def test_matrix_cross_tenant_isolated(
    auth_client, seeded_surahs, second_school_teacher
):
    """School A's students must not appear in school B's matrix."""
    a_id = await _create_student(auth_client, "School A Student")
    res = await second_school_teacher.get("/api/v1/students/matrix")
    body = res.json()
    assert all(s["id"] != a_id for s in body["students"])
