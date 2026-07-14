"""Tests for GET /api/v1/practice/v3/landing and practice_narration service."""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.narration.practice_narration import SYSTEM_INSTRUCTION


# ── narration service behavioural tests ─────────────────────────────────────


def test_practice_narration_system_instruction_bans_praise():
    """SYSTEM_INSTRUCTION must contain explicit guard against praise language."""
    lower = SYSTEM_INSTRUCTION.lower()
    assert "never praise" in lower or ("never" in lower and "praise" in lower), (
        "SYSTEM_INSTRUCTION must explicitly ban praise"
    )


def test_practice_narration_system_instruction_bans_speculation():
    """SYSTEM_INSTRUCTION must contain explicit guard against speculation."""
    lower = SYSTEM_INSTRUCTION.lower()
    assert "never speculate" in lower or ("never" in lower and "speculate" in lower), (
        "SYSTEM_INSTRUCTION must explicitly ban speculation"
    )


def test_practice_narration_system_instruction_requires_evidence():
    """SYSTEM_INSTRUCTION must require analytical/evidence-based language."""
    lower = SYSTEM_INSTRUCTION.lower()
    assert "analytical" in lower or "evidence" in lower or "observed" in lower, (
        "SYSTEM_INSTRUCTION must require evidence-based analytical language"
    )


def test_practice_narration_system_instruction_no_exclamation():
    """SYSTEM_INSTRUCTION must forbid exclamation marks."""
    lower = SYSTEM_INSTRUCTION.lower()
    assert "exclamation" in lower, (
        "SYSTEM_INSTRUCTION must forbid exclamation marks"
    )


# ── endpoint tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_practice_v3_landing_returns_narration_and_weak_topics(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Endpoint returns narration string and weak_topics list."""
    from app.db.models import MasteryState

    db_session.add_all([
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="integration_basics",
            mastery_score=0.15,
            total_attempts=3,
        ),
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="differentiation_basics",
            mastery_score=0.25,
            total_attempts=2,
        ),
    ])
    await db_session.flush()

    mock_narration = (
        "Integration Basics and Differentiation Basics account for most recent lost marks. "
        "Today's practice can address either."
    )
    with patch(
        "app.api.v1.endpoints.practice.practice_narration.generate",
        new=AsyncMock(return_value=mock_narration),
    ):
        r = await authed_client.get(
            "/api/v1/practice/v3/landing?subject=pure_mathematics"
        )

    assert r.status_code == 200
    body = r.json()
    assert body["narration"] == mock_narration
    assert isinstance(body["weak_topics"], list)
    assert len(body["weak_topics"]) == 2
    # weakest first
    assert body["weak_topics"][0]["id"] == "integration_basics"
    assert body["weak_topics"][1]["id"] == "differentiation_basics"


@pytest.mark.asyncio
async def test_practice_v3_landing_fresh_student_returns_empty_weak_topics(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Fresh student (no mastery data) returns empty weak_topics list."""
    mock_narration = "No practice data yet. Start a session to build your profile."
    with patch(
        "app.api.v1.endpoints.practice.practice_narration.generate",
        new=AsyncMock(return_value=mock_narration),
    ):
        r = await authed_client.get(
            "/api/v1/practice/v3/landing?subject=pure_mathematics"
        )

    assert r.status_code == 200
    body = r.json()
    assert body["weak_topics"] == []


@pytest.mark.asyncio
async def test_practice_v3_landing_unknown_subject_returns_404(
    authed_client, student_with_subject
):
    """Returns 404 for a subject the student has not configured."""
    r = await authed_client.get(
        "/api/v1/practice/v3/landing?subject=nonexistent_subject"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_practice_v3_landing_returns_at_most_two_weak_topics(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Even with many weak topics, only top 2 (weakest mastery) are returned."""
    from app.db.models import MasteryState

    db_session.add_all([
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="integration_basics",
            mastery_score=0.10,
            total_attempts=3,
        ),
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="differentiation_basics",
            mastery_score=0.20,
            total_attempts=2,
        ),
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="partial_fractions",
            mastery_score=0.30,
            total_attempts=4,
        ),
    ])
    await db_session.flush()

    with patch(
        "app.api.v1.endpoints.practice.practice_narration.generate",
        new=AsyncMock(return_value="narration text"),
    ):
        r = await authed_client.get(
            "/api/v1/practice/v3/landing?subject=pure_mathematics"
        )

    body = r.json()
    assert len(body["weak_topics"]) == 2
    ids = [t["id"] for t in body["weak_topics"]]
    assert "integration_basics" in ids
    assert "differentiation_basics" in ids
    assert "partial_fractions" not in ids
