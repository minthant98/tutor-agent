"""Tests for POST /api/v1/alex/session/{session_id}/message."""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.db.models import TutorSession


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_session(db_session, student_id: uuid.UUID) -> TutorSession:
    """Insert a minimal TutorSession owned by student_id."""
    sess = TutorSession(
        student_id=student_id,
        subject="pure_mathematics",
        topic="Integration",
        mode="explain",
        session_type="practice",
        session_version=2,
        segment_plan=[
            {
                "idx": 0,
                "intent": "assess",
                "handler": "practice",
                "topic": "Integration",
                "why": "Test segment",
                "target_minutes": 5,
                "status": "in_progress",
                "config": {
                    "current_question": "Find ∫ x² dx.",
                },
            }
        ],
        current_segment_idx=0,
        messages=[],
    )
    db_session.add(sess)
    await db_session.flush()
    return sess


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_alex_session_requires_auth(unauth_client):
    """Endpoint must return 401 when no Authorization header is provided."""
    fake_session_id = str(uuid.uuid4())
    r = await unauth_client.post(
        f"/api/v1/alex/session/{fake_session_id}/message",
        json={"text": "Help me."},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_alex_session_owned_session_streams_response(
    authed_client, db_session, student_with_subject
):
    """Authed student calling their own session gets an SSE response."""
    sess = await _create_session(db_session, student_with_subject.id)

    async def _fake_stream(*args, **kwargs):
        yield "Hello"
        yield " world"

    with patch(
        "app.api.v1.endpoints.alex_session.stream_alex_reply",
        new=_fake_stream,
    ):
        r = await authed_client.post(
            f"/api/v1/alex/session/{sess.id}/message",
            json={"text": "What should I do?"},
        )

    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")

    # Parse the SSE chunks
    chunks = [
        line[6:]  # strip "data: "
        for line in r.text.splitlines()
        if line.startswith("data: ")
    ]
    parsed = [json.loads(c) for c in chunks]

    delta_texts = [p["delta"] for p in parsed if "delta" in p]
    assert delta_texts == ["Hello", " world"]

    done_events = [p for p in parsed if p.get("done") is True]
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_alex_session_foreign_session_rejected(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    """A student cannot access another student's session — must get 403."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.db.database import get_db
    from app.core.auth import create_access_token
    from app.db.models import Student

    # Create second student
    other = Student(
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        name="Other Student",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=False,
    )
    db_session.add(other)
    await db_session.flush()

    # Session owned by student_with_subject
    sess = await _create_session(db_session, student_with_subject.id)

    # Client authenticated as `other`
    token = create_access_token({"sub": str(other.id)})

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            r = await client.post(
                f"/api/v1/alex/session/{sess.id}/message",
                json={"text": "What is this?"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert r.status_code == 403


@pytest.mark.asyncio
async def test_alex_session_missing_session_returns_404(authed_client):
    """Non-existent session_id must return 404."""
    fake_id = str(uuid.uuid4())
    r = await authed_client.post(
        f"/api/v1/alex/session/{fake_id}/message",
        json={"text": "Help."},
    )
    assert r.status_code == 404
