"""Analytics: per-student / per-class / per-school KPIs."""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_student(auth_client, name: str = "Bilal") -> str:
    return (
        await auth_client.post(
            "/api/v1/students", json={"full_name": name, "gender": "MALE"}
        )
    ).json()["id"]


async def test_student_analytics_no_progress(auth_client, seeded_surahs):
    """A fresh student has all surahs as NOT_STARTED (implicit) and 0% mastery."""
    sid = await _create_student(auth_client)
    res = await auth_client.get(f"/api/v1/analytics/student/{sid}")
    assert res.status_code == 200
    body = res.json()
    assert body["total_surahs"] == 2
    assert body["counts_by_status"]["NOT_STARTED"] == 2
    assert body["counts_by_status"]["MASTERED"] == 0
    assert body["mastery_percent"] == 0.0
    assert body["mastered_surah_ids"] == []
    assert body["recent_evaluations_count"] == 0
    assert body["recent_evaluations_avg_score"] is None


async def test_student_analytics_with_mixed_progress(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    # Surah 1: MASTERED, Surah 2: WEAK
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 2, "status": "WEAK", "completion_percent": 40},
    )

    res = await auth_client.get(f"/api/v1/analytics/student/{sid}")
    body = res.json()
    assert body["counts_by_status"]["MASTERED"] == 1
    assert body["counts_by_status"]["WEAK"] == 1
    assert body["counts_by_status"]["NOT_STARTED"] == 0
    assert body["mastery_percent"] == 50.0  # 1/2
    assert body["avg_completion_pct"] == 70.0  # mean of 100 and 40
    assert body["mastered_surah_ids"] == [1]
    assert body["weak_surah_ids"] == [2]


async def test_student_analytics_includes_evaluation_avg(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    for score in (80, 90, 100):
        await auth_client.post(
            f"/api/v1/students/{sid}/evaluations",
            json={"type": "ORAL_RECITATION", "exam_date": "2026-05-10", "overall_score": score},
        )
    res = await auth_client.get(f"/api/v1/analytics/student/{sid}")
    body = res.json()
    assert body["recent_evaluations_count"] == 3
    assert body["recent_evaluations_avg_score"] == 90.0


async def test_student_analytics_unknown(auth_client, seeded_surahs):
    res = await auth_client.get(
        "/api/v1/analytics/student/00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404


async def test_school_analytics(auth_client, seeded_surahs):
    s1 = await _create_student(auth_client, "Ahmed")
    s2 = await _create_student(auth_client, "Yusuf")

    # s1: both surahs MASTERED -> mastery 100%
    for surah_id in (1, 2):
        await auth_client.post(
            f"/api/v1/students/{s1}/progress",
            json={"surah_id": surah_id, "status": "MASTERED", "completion_percent": 100},
        )
    # s2: surah 1 only, STRONG -> mastery 0%
    await auth_client.post(
        f"/api/v1/students/{s2}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )

    res = await auth_client.get("/api/v1/analytics/school")
    assert res.status_code == 200
    body = res.json()
    assert body["student_count"] == 2
    # Average mastery: (2 + 0) / 2 / 2 surahs = 50%
    assert body["avg_mastery_percent"] == 50.0
    assert body["counts_by_status"]["MASTERED"] == 2
    assert body["counts_by_status"]["STRONG"] == 1
    # 4 expected slots (2 students * 2 surahs), 3 recorded -> 1 implicit NOT_STARTED
    assert body["counts_by_status"]["NOT_STARTED"] == 1



async def test_class_analytics(auth_client, session_factory, seeded_surahs):
    """Create a class, attach a student, verify class-level aggregates."""
    from app.models.class_ import Class

    # Create a class directly via the DB (no API for classes yet — coming in MVP-3 admin).
    me = (await auth_client.get("/api/v1/auth/me")).json()
    school_id = me["school_id"]

    async with session_factory() as db:
        klass = Class(school_id=school_id, name="Section A", academic_year="2025-2026")
        db.add(klass)
        await db.commit()
        await db.refresh(klass)
        class_id = str(klass.id)

    s1 = (
        await auth_client.post(
            "/api/v1/students",
            json={"full_name": "Ali", "gender": "MALE", "class_id": class_id},
        )
    ).json()["id"]

    await auth_client.post(
        f"/api/v1/students/{s1}/progress",
        json={"surah_id": 1, "status": "MASTERED", "completion_percent": 100},
    )

    res = await auth_client.get(f"/api/v1/analytics/class/{class_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["class_name"] == "Section A"
    assert body["student_count"] == 1
    assert body["counts_by_status"]["MASTERED"] == 1
    # 1 student * 2 surahs = 2 slots, 1 mastered -> 50%
    assert body["avg_mastery_percent"] == 50.0


async def test_class_analytics_unknown(auth_client, seeded_surahs):
    res = await auth_client.get(
        "/api/v1/analytics/class/00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404



async def test_evaluation_trend_buckets_by_month(auth_client, seeded_surahs):
    sid = await _create_student(auth_client, "Hamza")
    # Two evals in March, one in April, one in May
    payloads = [
        ("2026-03-05", 80),
        ("2026-03-25", 60),
        ("2026-04-10", 90),
        ("2026-05-15", 100),
    ]
    for exam_date, score in payloads:
        await auth_client.post(
            f"/api/v1/students/{sid}/evaluations",
            json={"type": "MONTHLY_REVIEW", "exam_date": exam_date, "overall_score": score},
        )

    res = await auth_client.get(
        f"/api/v1/analytics/student/{sid}/evaluation-trend?bucket=month"
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["bucket"] == "month"
    assert len(body["points"]) == 3
    assert body["points"][0]["period_start"] == "2026-03-01"
    assert body["points"][0]["avg_overall_score"] == 70.0  # mean(80, 60)
    assert body["points"][0]["eval_count"] == 2
    assert body["points"][1]["period_start"] == "2026-04-01"
    assert body["points"][1]["avg_overall_score"] == 90.0
    assert body["points"][2]["period_start"] == "2026-05-01"
    assert body["points"][2]["avg_overall_score"] == 100.0


async def test_evaluation_trend_buckets_by_week(auth_client, seeded_surahs):
    sid = await _create_student(auth_client, "Tariq")
    # Mon 2026-05-04 and Fri 2026-05-08 are in the same ISO week (week-of-Mon-2026-05-04)
    await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={"type": "ORAL_RECITATION", "exam_date": "2026-05-04", "overall_score": 70},
    )
    await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={"type": "ORAL_RECITATION", "exam_date": "2026-05-08", "overall_score": 90},
    )
    res = await auth_client.get(
        f"/api/v1/analytics/student/{sid}/evaluation-trend?bucket=week"
    )
    body = res.json()
    assert len(body["points"]) == 1
    assert body["points"][0]["period_start"] == "2026-05-04"
    assert body["points"][0]["avg_overall_score"] == 80.0


async def test_evaluation_trend_no_evals(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.get(f"/api/v1/analytics/student/{sid}/evaluation-trend")
    assert res.status_code == 200
    assert res.json()["points"] == []


async def test_evaluation_trend_invalid_bucket(auth_client, seeded_surahs):
    sid = await _create_student(auth_client)
    res = await auth_client.get(
        f"/api/v1/analytics/student/{sid}/evaluation-trend?bucket=quarter"
    )
    assert res.status_code == 422


async def test_evaluation_trend_unknown_student(auth_client, seeded_surahs):
    res = await auth_client.get(
        "/api/v1/analytics/student/00000000-0000-0000-0000-000000000000/evaluation-trend"
    )
    assert res.status_code == 404
