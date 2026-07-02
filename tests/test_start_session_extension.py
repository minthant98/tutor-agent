"""Tests for extended StartSessionRequest fields (Task 25 backend patch).

Verifies that:
- session_type="diagnostic" creates a session with exactly 7 segment entries
- session_type defaults to "practice" (no segment plan seeded)
- return_to is stored as system message in conversation history
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.db.models import TutorSession
from sqlalchemy import select


@pytest.mark.asyncio
async def test_diagnostic_session_creates_7_segments(authed_client, db_session):
    """POST /sessions/start with session_type=diagnostic should persist 7 segments."""
    with (
        patch(
            "app.api.v1.endpoints.sessions.generate_opening_message",
            new=AsyncMock(return_value="Let's begin your diagnostic."),
        ),
        patch("app.api.v1.endpoints.sessions.save_session"),
    ):
        r = await authed_client.post(
            "/api/v1/sessions/start",
            json={
                "subject": "pure_mathematics",
                "session_type": "diagnostic",
            },
        )

    assert r.status_code == 201, r.text
    body = r.json()
    assert "session_id" in body

    # Verify DB row has exactly 7 segments
    result = await db_session.execute(
        select(TutorSession).where(TutorSession.id == body["session_id"])
    )
    db_session_row = result.scalar_one()
    assert db_session_row.session_type == "diagnostic"
    assert len(db_session_row.segment_plan) == 7


@pytest.mark.asyncio
async def test_practice_session_no_segment_plan(authed_client, db_session):
    """POST /sessions/start with default session_type=practice has no auto-generated segments."""
    with (
        patch(
            "app.api.v1.endpoints.sessions.generate_opening_message",
            new=AsyncMock(return_value="Let's start your session."),
        ),
        patch("app.api.v1.endpoints.sessions.save_session"),
    ):
        r = await authed_client.post(
            "/api/v1/sessions/start",
            json={"subject": "pure_mathematics"},
        )

    assert r.status_code == 201, r.text
    body = r.json()

    result = await db_session.execute(
        select(TutorSession).where(TutorSession.id == body["session_id"])
    )
    db_session_row = result.scalar_one()
    assert db_session_row.session_type == "practice"
    assert len(db_session_row.segment_plan) == 0


@pytest.mark.asyncio
async def test_return_to_stored_as_system_message(authed_client):
    """POST /sessions/start with return_to should store it in session state."""
    captured_state = {}

    def _fake_save(state):
        captured_state.update(state)

    with (
        patch(
            "app.api.v1.endpoints.sessions.generate_opening_message",
            new=AsyncMock(return_value="Diagnostic ready."),
        ),
        patch("app.api.v1.endpoints.sessions.save_session", side_effect=_fake_save),
    ):
        r = await authed_client.post(
            "/api/v1/sessions/start",
            json={
                "subject": "pure_mathematics",
                "session_type": "diagnostic",
                "return_to": "/onboarding/preferences",
            },
        )

    assert r.status_code == 201, r.text
    history = captured_state.get("conversation_history", [])
    system_msgs = [m for m in history if m.get("role") == "system"]
    assert any(
        "return_to:/onboarding/preferences" in m.get("content", "")
        for m in system_msgs
    ), f"return_to not found in system messages: {system_msgs}"
