"""Tests for GET /api/v1/sessions/active sidebar endpoint.

The endpoint returns null when no in-progress session exists, or a
SidebarActiveSessionResponse with progress derived from segment_plan /
current_segment_idx when a session is open (ended_at IS NULL).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.db.models import Student, TutorSession
from app.main import app
from app.db.database import get_db
from app.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client_with_student(db_session):
    """Client authed as a simple student (no special subjects needed)."""
    s = Student(
        email="sidebar_test@example.com",
        name="Sidebar Test",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=True,
    )
    db_session.add(s)
    await db_session.flush()

    token = create_access_token({"sub": str(s.id)})

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            yield client, s
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def active_practice_session(db_session, client_with_student):
    """A TutorSession with ended_at=None, session_type=quick_practice, and
    a segment_plan matching 5 total / 3 completed (current_segment_idx=2)."""
    _, student = client_with_student
    session = TutorSession(
        student_id=student.id,
        subject="pure_mathematics",
        topic="integration_basics",
        session_type="quick_practice",
        mode="explain",
        segment_plan=[
            {"idx": 0, "intent": "question", "status": "done"},
            {"idx": 1, "intent": "question", "status": "done"},
            {"idx": 2, "intent": "question", "status": "in_progress"},
            {"idx": 3, "intent": "question", "status": "pending"},
            {"idx": 4, "intent": "question", "status": "pending"},
        ],
        current_segment_idx=2,  # 0-based → current_question = 3 (1-based)
        messages=[],
        ended_at=None,
    )
    db_session.add(session)
    await db_session.flush()
    return session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_active_session_returns_null_for_no_session(client_with_student):
    client, _ = client_with_student
    r = await client.get("/api/v1/sessions/active")
    assert r.status_code == 200
    assert r.json() is None


@pytest.mark.asyncio
async def test_active_session_returns_practice_progress(
    client_with_student, active_practice_session
):
    client, _ = client_with_student
    r = await client.get("/api/v1/sessions/active")
    assert r.status_code == 200
    body = r.json()
    assert body is not None
    assert body["session_id"] == str(active_practice_session.id)
    assert body["topic"] == "integration_basics"
    assert body["session_type"] == "quick_practice"
    assert body["progress"]["current_question"] == 3   # current_segment_idx+1
    assert body["progress"]["total_questions"] == 5    # len(segment_plan)


@pytest.mark.asyncio
async def test_active_session_requires_auth(db_session):
    """Unauthenticated request → 401."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            r = await client.get("/api/v1/sessions/active")
            assert r.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_active_session_ended_session_not_returned(
    client_with_student, db_session
):
    """A session with ended_at set should not be returned."""
    from datetime import datetime, timezone
    _, student = client_with_student
    session = TutorSession(
        student_id=student.id,
        subject="pure_mathematics",
        topic="integration_basics",
        session_type="quick_practice",
        mode="explain",
        segment_plan=[],
        current_segment_idx=0,
        messages=[],
        ended_at=datetime.now(timezone.utc),
    )
    db_session.add(session)
    await db_session.flush()

    client, _ = client_with_student
    r = await client.get("/api/v1/sessions/active")
    assert r.status_code == 200
    assert r.json() is None
