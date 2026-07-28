"""Tests for GET /api/v1/progress/v3 — progress v3 endpoint."""
import pytest
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4


@pytest.mark.asyncio
async def test_progress_v3_requires_auth(unauth_client, student_with_subject):
    """Endpoint returns 401 when unauthenticated."""
    r = await unauth_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_progress_v3_unknown_subject_404(authed_client, student_with_subject):
    """Unknown subject returns 404."""
    r = await authed_client.get("/api/v1/progress/v3?subject=nonexistent_xyz")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_progress_v3_returns_shape(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """Endpoint returns expected top-level keys."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    for key in (
        "narration", "chart_series", "readiness_current",
        "readiness_delta_14d", "mastery_by_topic",
        "session_history", "marker_history_compact", "weekly_stats",
    ):
        assert key in body, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_progress_v3_chart_series_length(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """chart_series has exactly `days` entries."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics&days=30")
    assert r.status_code == 200
    body = r.json()
    assert len(body["chart_series"]) == 30


@pytest.mark.asyncio
async def test_progress_v3_chart_series_90_days(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """chart_series has exactly 90 entries when days=90."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics&days=90")
    assert r.status_code == 200
    body = r.json()
    assert len(body["chart_series"]) == 90


@pytest.mark.asyncio
async def test_progress_v3_chart_point_shape(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """Each chart_series entry has date (str) and readiness (int)."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    for point in body["chart_series"]:
        assert "date" in point
        assert "readiness" in point
        assert isinstance(point["readiness"], int)
        # date must be YYYY-MM-DD
        assert len(point["date"]) == 10


@pytest.mark.asyncio
async def test_progress_v3_weekly_stats_shape(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """weekly_stats has expected numeric fields."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    weekly = r.json()["weekly_stats"]
    for key in ("sessions_this_week", "questions_attempted", "marks_scored", "marks_max", "time_in_app_minutes"):
        assert key in weekly
        assert isinstance(weekly[key], int)


@pytest.mark.asyncio
async def test_progress_v3_session_history_from_db(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Sessions for the student appear in session_history."""
    from app.db.models import TutorSession
    now = datetime.now(timezone.utc)
    session = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="quick_practice",
        topic="integration_basics",
        started_at=now - timedelta(minutes=15),
        ended_at=now,
    )
    db_session.add(session)
    await db_session.flush()

    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    ids = [s["id"] for s in body["session_history"]]
    assert str(session.id) in ids


@pytest.mark.asyncio
async def test_progress_v3_session_history_at_most_20(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """session_history is capped at 20 items."""
    from app.db.models import TutorSession
    now = datetime.now(timezone.utc)
    for i in range(25):
        db_session.add(TutorSession(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            mode="practice",
            started_at=now - timedelta(hours=i + 1),
            ended_at=now - timedelta(hours=i),
        ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    assert len(r.json()["session_history"]) <= 20


@pytest.mark.asyncio
async def test_progress_v3_readiness_delta_zero_no_snapshots(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """readiness_delta_14d is 0 when there are no historical snapshots."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    assert r.json()["readiness_delta_14d"] == 0


@pytest.mark.asyncio
async def test_progress_v3_narration_is_string(authed_client, student_with_subject, syllabus_edexcel_seeded):
    """narration field is a non-empty string."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    narration = r.json()["narration"]
    assert isinstance(narration, str)
    assert len(narration) > 0


@pytest.mark.asyncio
async def test_progress_v3_mastery_by_topic_shape(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """mastery_by_topic items have id, label, and mastery (int)."""
    r = await authed_client.get("/api/v1/progress/v3?subject=pure_mathematics")
    assert r.status_code == 200
    topics = r.json()["mastery_by_topic"]
    assert isinstance(topics, list)
    for t in topics:
        assert "id" in t
        assert "label" in t
        assert "mastery" in t
        assert isinstance(t["mastery"], int)
        assert 0 <= t["mastery"] <= 100
