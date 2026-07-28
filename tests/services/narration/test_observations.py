"""Tests for app/services/narration/observations.py

Covers:
- SYSTEM_INSTRUCTION content (no praise, behavioral guards)
- Cap of 3
- Anti-hallucination: items with unknown trace_ref dropped
- Every persisted observation has non-empty trace
- Fresh student with no data returns empty list
"""
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.db.models import MasteryState
from app.services.narration import observations as obs_module


# ---------------------------------------------------------------------------
# SYSTEM_INSTRUCTION behavioral assertions (no DB needed)
# ---------------------------------------------------------------------------

def test_system_instruction_bans_praise():
    s = obs_module.SYSTEM_INSTRUCTION.lower()
    for banned in ["never praise", "great job", "well done", "amazing", "keep it up", "you're crushing"]:
        assert banned in s, f"SYSTEM_INSTRUCTION must ban '{banned}'"


def test_system_instruction_bans_speculation():
    s = obs_module.SYSTEM_INSTRUCTION.lower()
    assert "never speculate" in s


def test_system_instruction_forbids_student_name():
    s = obs_module.SYSTEM_INSTRUCTION.lower()
    assert "student's name" in s or "do not use the student" in s


def test_system_instruction_forbids_exclamation():
    s = obs_module.SYSTEM_INSTRUCTION.lower()
    assert "exclamation" in s


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def subject():
    return "pure_mathematics"


@pytest.fixture
def week_of():
    return date(2026, 7, 7)  # a Monday


# ---------------------------------------------------------------------------
# Helper: patch LLM to return controlled responses
# ---------------------------------------------------------------------------

def _make_llm_response(items: list[dict]):
    """Return an AsyncMock for llm.generate_json that returns `items`."""
    return AsyncMock(return_value=items)


def _add_weak_mastery(db_session, student_id, subject, topic):
    ms = MasteryState(
        student_id=student_id,
        subject=subject,
        topic=topic,
        mastery_score=0.2,
        is_weak=True,
        total_attempts=5,
        correct_streak=0,
    )
    db_session.add(ms)
    return ms


# ---------------------------------------------------------------------------
# test_capped_at_three
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_capped_at_three(db_session, student, subject, week_of):
    """Even if LLM returns 5 items, only 3 observations are persisted."""
    _add_weak_mastery(db_session, student.id, subject, "integration")
    await db_session.flush()

    # LLM returns 5 items all referencing "mastery_weak_topics"
    five_items = [
        {"text": f"Observation {i}.", "trace_ref": "mastery_weak_topics"}
        for i in range(5)
    ]
    with patch.object(obs_module.llm, "generate_json", new=_make_llm_response(five_items)):
        result = await obs_module.generate_for_week(db_session, student.id, subject, week_of)

    assert len(result) <= 3, f"Expected ≤3 but got {len(result)}"


# ---------------------------------------------------------------------------
# test_carries_trace_with_session_ids_or_queries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_carries_trace_with_session_ids_or_queries(db_session, student, subject, week_of):
    """Every persisted observation must have non-empty queries OR non-empty session_ids."""
    _add_weak_mastery(db_session, student.id, subject, "calculus")
    await db_session.flush()

    two_items = [
        {"text": "Calculus mastery remains low.", "trace_ref": "mastery_weak_topics"},
        {"text": "No improvement on weak topics.", "trace_ref": "mastery_weak_topics"},
    ]
    with patch.object(obs_module.llm, "generate_json", new=_make_llm_response(two_items)):
        result = await obs_module.generate_for_week(db_session, student.id, subject, week_of)

    assert len(result) > 0, "Expected at least one observation"
    for observation in result:
        tj = observation.trace_json
        assert "queries" in tj
        assert "session_ids" in tj
        # Non-empty queries OR non-empty session_ids
        assert tj["queries"] or tj["session_ids"], (
            f"trace_json must have non-empty queries or session_ids; got {tj}"
        )


# ---------------------------------------------------------------------------
# test_hallucinated_items_dropped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hallucinated_items_dropped(db_session, student, subject, week_of):
    """LLM returns an item with a trace_ref not in the evidence dict — it must be dropped."""
    _add_weak_mastery(db_session, student.id, subject, "statistics")
    await db_session.flush()

    hallucinated_and_valid = [
        {"text": "This is hallucinated.", "trace_ref": "nonexistent_key_123"},
        {"text": "Mastery on statistics is critically low.", "trace_ref": "mastery_weak_topics"},
    ]
    with patch.object(obs_module.llm, "generate_json", new=_make_llm_response(hallucinated_and_valid)):
        result = await obs_module.generate_for_week(db_session, student.id, subject, week_of)

    texts = [r.text for r in result]
    assert not any("hallucinated" in t.lower() for t in texts), (
        "Hallucinated item should have been dropped"
    )
    assert len(result) == 1
    assert "mastery" in result[0].text.lower() or "statistics" in result[0].text.lower()


# ---------------------------------------------------------------------------
# test_fresh_student_returns_empty_list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fresh_student_returns_empty_list(db_session, subject, week_of):
    """A student with no data → empty result, no LLM call."""
    fresh_id = uuid.uuid4()  # not in students table; no FK needed for the select
    with patch.object(obs_module.llm, "generate_json", new=AsyncMock()) as mock_llm:
        result = await obs_module.generate_for_week(db_session, fresh_id, subject, week_of)
    assert result == [], f"Expected [] but got {result}"
    mock_llm.assert_not_called()


# ---------------------------------------------------------------------------
# test_system_instruction_passed_to_llm
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_system_instruction_passed_to_llm(db_session, student, subject, week_of):
    """generate_for_week must pass SYSTEM_INSTRUCTION to llm.generate_json."""
    _add_weak_mastery(db_session, student.id, subject, "algebra")
    await db_session.flush()

    with patch.object(obs_module.llm, "generate_json", new=AsyncMock(return_value=[])) as m:
        await obs_module.generate_for_week(db_session, student.id, subject, week_of)

    m.assert_called_once()
    kwargs = m.call_args.kwargs
    assert kwargs.get("system") == obs_module.SYSTEM_INSTRUCTION, (
        "SYSTEM_INSTRUCTION not passed to generate_json"
    )
