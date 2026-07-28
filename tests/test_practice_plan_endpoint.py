"""Tests for GET /api/v1/practice/plan and GET /api/v1/practice/drill-in/resume."""
import pytest
from unittest.mock import AsyncMock, patch


# ── GET /practice/plan ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_endpoint_returns_segments(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Plan endpoint returns segments, minutes and narration for drill_in mode."""
    with patch(
        "app.api.v1.endpoints.practice.practice_narration.generate",
        new=AsyncMock(return_value="Drill session on integration basics."),
    ):
        r = await authed_client.get(
            "/api/v1/practice/plan?mode=drill_in&topic=integration_basics"
        )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["segments"], list)
    assert len(body["segments"]) == 3  # teach, reinforce, assess
    assert body["minutes"] > 0
    assert body["narration"]
    # All segments have intent and topic
    for seg in body["segments"]:
        assert "intent" in seg
        assert "topic" in seg


@pytest.mark.asyncio
async def test_plan_endpoint_marker_bridge_updates_narration(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """When skill param is present, narration mentions Exam Marker."""
    r = await authed_client.get(
        "/api/v1/practice/plan?mode=drill_in&topic=integration_basics&skill=substitution"
    )
    assert r.status_code == 200
    body = r.json()
    assert "Exam Marker" in body["narration"] or "coming from" in body["narration"].lower()
    # First segment topic matches the requested topic (integration_basics)
    # (topic_id or its display name)
    assert any("integration" in seg["topic"].lower() for seg in body["segments"])


@pytest.mark.asyncio
async def test_plan_endpoint_unknown_mode_returns_400(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await authed_client.get("/api/v1/practice/plan?mode=nonexistent")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_plan_endpoint_drill_in_requires_topic(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await authed_client.get("/api/v1/practice/plan?mode=drill_in")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_plan_endpoint_weak_areas_no_topic_required(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    with patch(
        "app.api.v1.endpoints.practice.practice_narration.generate",
        new=AsyncMock(return_value="Weak areas narration."),
    ):
        r = await authed_client.get("/api/v1/practice/plan?mode=weak_areas")
    # weak_areas may return 200 or 0 segments depending on mastery data — just check no 4xx
    assert r.status_code == 200


# ── GET /practice/drill-in/resume ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drill_in_resume_returns_null_when_no_active_session(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await authed_client.get("/api/v1/practice/drill-in/resume?topic=integration_basics")
    assert r.status_code == 200
    assert r.json() is None


@pytest.mark.asyncio
async def test_drill_in_resume_returns_valid_shape_for_active_session(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Returns session_id, topic_label, progress when an active drill_in session exists."""
    from app.db.models import TutorSession

    session = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="drill_in",
        segment_plan=[
            {"idx": 0, "intent": "teach", "topic": "integration_basics", "status": "in_progress"},
            {"idx": 1, "intent": "reinforce", "topic": "integration_basics", "status": "pending"},
            {"idx": 2, "intent": "assess", "topic": "integration_basics", "status": "pending"},
        ],
        current_segment_idx=1,
        ended_at=None,
    )
    db_session.add(session)
    await db_session.flush()

    r = await authed_client.get("/api/v1/practice/drill-in/resume?topic=integration_basics")
    assert r.status_code == 200
    body = r.json()
    assert body is not None
    assert "session_id" in body
    assert "topic_label" in body
    assert "progress" in body
    assert body["progress"]["current"] == 1
    assert body["progress"]["total"] == 3


@pytest.mark.asyncio
async def test_drill_in_resume_returns_null_for_different_topic(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Returns null when active session is for a different topic."""
    from app.db.models import TutorSession

    session = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="drill_in",
        segment_plan=[
            {"idx": 0, "intent": "teach", "topic": "differentiation_basics", "status": "in_progress"},
        ],
        current_segment_idx=0,
        ended_at=None,
    )
    db_session.add(session)
    await db_session.flush()

    r = await authed_client.get("/api/v1/practice/drill-in/resume?topic=integration_basics")
    assert r.status_code == 200
    assert r.json() is None
