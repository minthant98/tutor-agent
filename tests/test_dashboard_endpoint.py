"""Tests for GET /api/v1/dashboard/{subject} endpoint."""
import pytest


@pytest.mark.asyncio
async def test_dashboard_returns_payload(authed_client, student_with_subject):
    res = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "readiness_pct" in body
    assert "today_focus" in body
    assert body["target_grade"] == "A*"


@pytest.mark.asyncio
async def test_dashboard_404_for_unsupported_subject(authed_client):
    res = await authed_client.get("/api/v1/dashboard/physics")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_payload_fields(authed_client, student_with_subject):
    res = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert res.status_code == 200, res.text
    body = res.json()
    required_top_level = {
        "subject", "exam_date", "days_until_exam", "target_grade",
        "predicted_grade", "readiness_pct", "readiness_trend",
        "today_focus", "resume_session", "recent_activity",
        "strong_topics", "weak_topics", "subject_options",
    }
    assert required_top_level.issubset(set(body.keys()))
    # today_focus should have 3 segments
    assert len(body["today_focus"]["segment_plan"]) == 3
    # subject_options should include the configured subject
    assert "pure_mathematics" in body["subject_options"]


@pytest.mark.asyncio
async def test_dashboard_today_focus_shape(authed_client, student_with_subject):
    res = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert res.status_code == 200, res.text
    body = res.json()
    valid_shapes = {"onboarding", "build", "default", "exam_ready"}
    assert body["today_focus"]["shape"] in valid_shapes


@pytest.mark.asyncio
async def test_dashboard_no_resume_session_by_default(authed_client, student_with_subject):
    res = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert res.status_code == 200, res.text
    body = res.json()
    # No open sessions were created, so resume_session should be None
    assert body["resume_session"] is None
