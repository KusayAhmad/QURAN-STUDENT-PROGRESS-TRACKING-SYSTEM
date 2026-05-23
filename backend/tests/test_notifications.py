"""Notification production + per-user inbox API."""
import pytest

pytestmark = pytest.mark.asyncio

# Reuse admin_client fixture
pytest_plugins = ["tests.test_audit_log"]


async def test_unread_count_starts_at_zero(auth_client):
    res = await auth_client.get("/api/v1/notifications/unread-count")
    assert res.status_code == 200
    assert res.json() == {"unread": 0}


async def test_student_added_notifies_admins_not_actor(admin_client, auth_client):
    """A teacher creates a student. The admin gets notified, the teacher does not."""
    await auth_client.post(
        "/api/v1/students", json={"full_name": "Notif Student", "gender": "MALE"}
    )

    # Admin sees one notification.
    admin_count = await admin_client.get("/api/v1/notifications/unread-count")
    assert admin_count.json()["unread"] == 1

    admin_list = await admin_client.get("/api/v1/notifications")
    items = admin_list.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "STUDENT_ADDED"
    assert "Notif Student" in items[0]["title"]

    # The teacher (the actor) should NOT be pinged for their own action.
    teacher_count = await auth_client.get("/api/v1/notifications/unread-count")
    assert teacher_count.json()["unread"] == 0


async def test_admin_creating_student_notifies_no_one(admin_client):
    """Lone admin creates a student: no one to notify (actor excluded)."""
    await admin_client.post(
        "/api/v1/students", json={"full_name": "Solo", "gender": "MALE"}
    )
    res = await admin_client.get("/api/v1/notifications/unread-count")
    assert res.json()["unread"] == 0


async def test_progress_regression_triggers_notification(
    admin_client, auth_client, seeded_surahs
):
    """STRONG → WEAK on Al-Baqarah notifies the admin."""
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Reg Test", "gender": "MALE"}
        )
    ).json()["id"]

    # Initial state is STRONG.
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 2, "status": "STRONG", "completion_percent": 80},
    )
    # Drain admin's existing STUDENT_ADDED notification so we count cleanly.
    await admin_client.post("/api/v1/notifications/read-all")

    # Now regress.
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 2, "status": "WEAK", "completion_percent": 30},
    )

    listing = await admin_client.get("/api/v1/notifications?unread_only=true")
    items = listing.json()["items"]
    types = [n["type"] for n in items]
    assert "PROGRESS_REGRESSED" in types
    regression = next(n for n in items if n["type"] == "PROGRESS_REGRESSED")
    assert "Al-Baqarah" in regression["title"]
    assert "STRONG" in regression["message"] and "WEAK" in regression["message"]


async def test_progress_status_unchanged_no_notification(
    admin_client, auth_client, seeded_surahs
):
    """Re-saving the same status (a common no-op write) must not spam."""
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "NoChange", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )
    await admin_client.post("/api/v1/notifications/read-all")
    # Same status again
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 90},
    )
    res = await admin_client.get("/api/v1/notifications/unread-count")
    assert res.json()["unread"] == 0


async def test_progress_improvement_no_notification(
    admin_client, auth_client, seeded_surahs
):
    """WEAK → STRONG is an improvement, not a regression. No alert."""
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Improving", "gender": "MALE"}
        )
    ).json()["id"]
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "WEAK", "completion_percent": 20},
    )
    await admin_client.post("/api/v1/notifications/read-all")
    await auth_client.post(
        f"/api/v1/students/{sid}/progress",
        json={"surah_id": 1, "status": "STRONG", "completion_percent": 80},
    )
    res = await admin_client.get("/api/v1/notifications/unread-count")
    assert res.json()["unread"] == 0


async def test_low_evaluation_triggers_notification(admin_client, auth_client):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "Low Score", "gender": "FEMALE"}
        )
    ).json()["id"]
    await admin_client.post("/api/v1/notifications/read-all")

    # Score below threshold (60) -> notification
    await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={
            "type": "ORAL_RECITATION",
            "exam_date": "2026-05-10",
            "overall_score": 40,
        },
    )
    listing = await admin_client.get("/api/v1/notifications")
    types = [n["type"] for n in listing.json()["items"]]
    assert "LOW_EVALUATION" in types


async def test_high_evaluation_no_notification(admin_client, auth_client):
    sid = (
        await auth_client.post(
            "/api/v1/students", json={"full_name": "High Score", "gender": "MALE"}
        )
    ).json()["id"]
    await admin_client.post("/api/v1/notifications/read-all")
    await auth_client.post(
        f"/api/v1/students/{sid}/evaluations",
        json={
            "type": "MONTHLY_REVIEW",
            "exam_date": "2026-05-10",
            "overall_score": 90,
        },
    )
    res = await admin_client.get("/api/v1/notifications/unread-count")
    assert res.json()["unread"] == 0


async def test_mark_read_single(admin_client, auth_client):
    await auth_client.post(
        "/api/v1/students", json={"full_name": "Mark Read Test", "gender": "MALE"}
    )
    listing = await admin_client.get("/api/v1/notifications")
    nid = listing.json()["items"][0]["id"]
    assert listing.json()["items"][0]["read_at"] is None

    res = await admin_client.post(f"/api/v1/notifications/{nid}/read")
    assert res.status_code == 200
    assert res.json()["read_at"] is not None

    count = await admin_client.get("/api/v1/notifications/unread-count")
    assert count.json()["unread"] == 0


async def test_mark_read_idempotent(admin_client, auth_client):
    await auth_client.post(
        "/api/v1/students", json={"full_name": "Idem Read", "gender": "MALE"}
    )
    listing = await admin_client.get("/api/v1/notifications")
    nid = listing.json()["items"][0]["id"]
    first = await admin_client.post(f"/api/v1/notifications/{nid}/read")
    second = await admin_client.post(f"/api/v1/notifications/{nid}/read")
    assert first.json()["read_at"] == second.json()["read_at"]


async def test_mark_read_other_user_404(admin_client, auth_client, second_school_teacher):
    """A user cannot mark another user's notification as read."""
    # Create a real notification for admin_client.
    await auth_client.post(
        "/api/v1/students", json={"full_name": "Cross User", "gender": "MALE"}
    )
    listing = await admin_client.get("/api/v1/notifications")
    nid = listing.json()["items"][0]["id"]

    # second_school_teacher tries to mark admin's notification as read -> 404.
    res = await second_school_teacher.post(f"/api/v1/notifications/{nid}/read")
    assert res.status_code == 404


async def test_mark_all_read(admin_client, auth_client):
    # Generate three notifications
    for name in ("A", "B", "C"):
        await auth_client.post(
            "/api/v1/students", json={"full_name": f"Bulk {name}", "gender": "MALE"}
        )

    before = await admin_client.get("/api/v1/notifications/unread-count")
    assert before.json()["unread"] == 3

    res = await admin_client.post("/api/v1/notifications/read-all")
    assert res.json() == {"updated": 3}

    after = await admin_client.get("/api/v1/notifications/unread-count")
    assert after.json()["unread"] == 0


async def test_unread_only_filter(admin_client, auth_client):
    await auth_client.post(
        "/api/v1/students", json={"full_name": "Filter Test", "gender": "MALE"}
    )
    listing = await admin_client.get("/api/v1/notifications?unread_only=true")
    assert listing.json()["total"] == 1

    nid = listing.json()["items"][0]["id"]
    await admin_client.post(f"/api/v1/notifications/{nid}/read")

    after_unread = await admin_client.get("/api/v1/notifications?unread_only=true")
    after_all = await admin_client.get("/api/v1/notifications")
    assert after_unread.json()["total"] == 0
    assert after_all.json()["total"] == 1


async def test_notifications_per_user_isolated(
    admin_client, second_school_teacher, auth_client
):
    """School A activity must NOT show up in School B teacher's inbox."""
    await auth_client.post(
        "/api/v1/students", json={"full_name": "School A Action", "gender": "MALE"}
    )
    other_inbox = await second_school_teacher.get(
        "/api/v1/notifications/unread-count"
    )
    assert other_inbox.json()["unread"] == 0


async def test_notifications_require_auth(client):
    res = await client.get("/api/v1/notifications")
    assert res.status_code == 401
