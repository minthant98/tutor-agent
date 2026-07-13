"""Tests for GET /api/v1/dashboard/v3/{subject}."""
import pytest
import pytest_asyncio
import uuid as _uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


@pytest_asyncio.fixture
async def v3_student_with_subject(db_session, syllabus_edexcel_seeded):
    """Student + non-draft LearnerSubject for v3 endpoint tests."""
    from app.db.models import Student, LearnerSubject

    s = Student(
        email=f"v3_student_{_uuid.uuid4().hex[:8]}@example.com",
        name="V3 Student",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=True,
    )
    db_session.add(s)
    await db_session.flush()

    ls = LearnerSubject(
        student_id=s.id,
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
        target_grade="A",
        syllabus_version="2026.1",
        exam_date=date.today() + timedelta(days=42),
        is_draft=False,
    )
    db_session.add(ls)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def v3_authed_client(db_session, v3_student_with_subject):
    """httpx AsyncClient authenticated as v3_student_with_subject."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.db.database import get_db
    from app.core.auth import create_access_token

    token = create_access_token({"sub": str(v3_student_with_subject.id)})

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_dashboard_v3_returns_full_payload(v3_authed_client):
    """Endpoint returns all required top-level keys with valid values."""
    # Mock LLM generate so we don't need real API keys in tests
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with (
        patch("app.services.narration.dashboard_narration.llm.generate",
              new=AsyncMock(return_value="Recent mastery data targets integration basics today.")),
        patch("app.api.v1.endpoints.dashboard_v3.get_redis", return_value=mock_redis),
    ):
        r = await v3_authed_client.get("/api/v1/dashboard/v3/pure_mathematics")

    assert r.status_code == 200, r.text
    body = r.json()
    assert "narration" in body
    assert "readiness_snapshot" in body
    assert "session_plan" in body
    assert "total_minutes" in body
    assert "resume_state" in body

    snap = body["readiness_snapshot"]
    assert snap["percent"] >= 0
    assert snap["target_grade"] == "A"
    assert snap["band"] in ("A*", "A", "B", "C")
    assert snap["days_to_exam"] == 42

    # Plan: 3 segments from today_focus_service
    assert len(body["session_plan"]) == 3
    for seg in body["session_plan"]:
        assert "intent" in seg
        assert "topic" in seg
        assert "why" in seg
        assert "minutes" in seg

    # No active session → resume_state is None
    assert body["resume_state"] is None


@pytest.mark.asyncio
async def test_dashboard_v3_404_unknown_subject(v3_authed_client):
    """Endpoint returns 404 for a subject not configured for this student."""
    mock_redis = MagicMock()
    with patch("app.core.redis_client.get_redis", return_value=mock_redis):
        r = await v3_authed_client.get("/api/v1/dashboard/v3/physics")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_v3_unauthenticated(unauth_client):
    """Endpoint returns 401 when no auth header is supplied."""
    r = await unauth_client.get("/api/v1/dashboard/v3/pure_mathematics")
    assert r.status_code == 401
