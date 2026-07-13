"""Tests for GET /api/v1/observations/current-week?subject=<subject>

Covers:
- 401 without auth token
- Cache-hit: second call in same week returns same rows (no LLM call)
- Cache-miss: first call generates + persists observations
"""
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.db.models import MasteryState, Observation
from app.services.narration import observations as obs_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def obs_student(db_session):
    """Student used for observation endpoint tests."""
    from app.db.models import Student

    s = Student(
        email=f"obs_student_{uuid.uuid4().hex[:8]}@example.com",
        name="Obs Student",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=True,
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def obs_authed_client(db_session, obs_student):
    """Authenticated httpx client for observation endpoint tests."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.db.database import get_db
    from app.core.auth import create_access_token

    token = create_access_token({"sub": str(obs_student.id)})

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


# ---------------------------------------------------------------------------
# Test: 401 without token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_current_week_requires_auth(unauth_client):
    """Endpoint must return 401 when called without an Authorization header."""
    resp = await unauth_client.get(
        "/api/v1/observations/current-week?subject=pure_mathematics"
    )
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test: cache-miss → generates and persists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_call_generates_observations(db_session, obs_authed_client, obs_student):
    """First call (cache-miss) calls generate_for_week and returns results."""
    # Seed mastery data so evidence is non-empty
    ms = MasteryState(
        student_id=obs_student.id,
        subject="pure_mathematics",
        topic="calculus",
        mastery_score=0.2,
        is_weak=True,
        total_attempts=3,
        correct_streak=0,
    )
    db_session.add(ms)
    await db_session.flush()

    stubbed_llm = [
        {"text": "Calculus mastery score sits at 0.20.", "trace_ref": "mastery_weak_topics"},
    ]

    with patch.object(obs_service.llm, "generate_json", new=AsyncMock(return_value=stubbed_llm)):
        resp = await obs_authed_client.get(
            "/api/v1/observations/current-week?subject=pure_mathematics"
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    obs = body[0]
    assert "id" in obs
    assert "text" in obs
    assert "computed_at" in obs
    # trace_json must NOT be in the API response
    assert "trace_json" not in obs
    assert "calculus" in obs["text"].lower() or "mastery" in obs["text"].lower()


# ---------------------------------------------------------------------------
# Test: cache-hit → returns same rows, no LLM call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_second_call_returns_cached_rows(db_session, obs_authed_client, obs_student):
    """Second call in the same week returns existing DB rows without calling the LLM."""
    from datetime import datetime, timezone
    from app.api.v1.endpoints.observations import _current_week_start

    week_of = _current_week_start()

    # Pre-seed an observation so cache-hit triggers
    existing = Observation(
        student_id=obs_student.id,
        subject="pure_mathematics",
        text="Cached observation text.",
        trace_json={"queries": ["mastery_delta_last_7d"], "session_ids": [], "evidence_summary": "test"},
        week_of=week_of,
        computed_at=datetime.now(timezone.utc),
    )
    db_session.add(existing)
    await db_session.flush()

    with patch.object(obs_service.llm, "generate_json", new=AsyncMock()) as mock_llm:
        resp = await obs_authed_client.get(
            "/api/v1/observations/current-week?subject=pure_mathematics"
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["text"] == "Cached observation text."
    # LLM must NOT have been called
    mock_llm.assert_not_called()
