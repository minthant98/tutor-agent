"""Tests for app/services/alex/session_chat.py."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.db.models import TutorSession
from app.services.alex import session_chat


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_session(
    student_id: uuid.UUID | None = None,
    topic: str = "Integration",
    segment_plan: list | None = None,
    current_segment_idx: int = 0,
) -> TutorSession:
    s = MagicMock(spec=TutorSession)
    s.id = uuid.uuid4()
    s.student_id = student_id or uuid.uuid4()
    s.topic = topic
    s.segment_plan = segment_plan or []
    s.current_segment_idx = current_segment_idx
    return s


def _make_db(session: TutorSession | None) -> AsyncMock:
    """Return a mock AsyncSession whose execute().scalar_one_or_none() returns `session`."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = session
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


# ── 1. build_context returns current_question ─────────────────────────────────

@pytest.mark.asyncio
async def test_session_chat_context_includes_current_question():
    """build_context must surface the current question from segment config."""
    student_id = uuid.uuid4()
    plan = [
        {
            "idx": 0,
            "intent": "assess",
            "handler": "practice",
            "topic": "Integration",
            "why": "Test",
            "target_minutes": 5,
            "status": "in_progress",
            "config": {
                "current_question": "Integrate x^2 with respect to x.",
                "questions_asked": 1,
            },
        }
    ]
    session = _make_session(student_id=student_id, segment_plan=plan, current_segment_idx=0)
    db = _make_db(session)

    ctx = await session_chat.build_context(db, str(student_id), str(session.id))

    assert ctx["current_question"] == "Integrate x^2 with respect to x."
    assert ctx["current_segment_intent"] in ("teach", "reinforce", "assess", "diagnose", "revise", "consolidate")


@pytest.mark.asyncio
async def test_session_chat_context_intent_is_returned():
    """build_context must return the current segment's intent."""
    student_id = uuid.uuid4()
    plan = [
        {
            "idx": 0,
            "intent": "reinforce",
            "handler": "practice",
            "topic": "Differentiation",
            "why": "Test",
            "target_minutes": 5,
            "status": "in_progress",
            "config": {},
        }
    ]
    session = _make_session(student_id=student_id, segment_plan=plan)
    db = _make_db(session)

    ctx = await session_chat.build_context(db, str(student_id), str(session.id))

    assert ctx["current_segment_intent"] == "reinforce"


@pytest.mark.asyncio
async def test_session_chat_context_handles_empty_plan():
    """build_context should return None fields gracefully when segment_plan is empty."""
    student_id = uuid.uuid4()
    session = _make_session(student_id=student_id, segment_plan=[])
    db = _make_db(session)

    ctx = await session_chat.build_context(db, str(student_id), str(session.id))

    assert ctx["current_question"] is None
    assert ctx["current_segment_intent"] is None


@pytest.mark.asyncio
async def test_session_chat_context_handles_question_as_dict():
    """build_context must handle current_question stored as a dict (Qdrant doc shape)."""
    student_id = uuid.uuid4()
    plan = [
        {
            "idx": 0,
            "intent": "assess",
            "handler": "practice",
            "topic": "Vectors",
            "why": "Test",
            "target_minutes": 5,
            "status": "in_progress",
            "config": {
                "current_question": {
                    "question_text": "Find the magnitude of vector (3, 4).",
                    "difficulty": "easy",
                },
            },
        }
    ]
    session = _make_session(student_id=student_id, segment_plan=plan)
    db = _make_db(session)

    ctx = await session_chat.build_context(db, str(student_id), str(session.id))

    assert ctx["current_question"] == "Find the magnitude of vector (3, 4)."


# ── 2. SYSTEM_INSTRUCTION behavioural test ────────────────────────────────────

def test_session_chat_prompt_forbids_invention():
    """SYSTEM_INSTRUCTION must contain the invention-guard phrase."""
    system_lower = session_chat.SYSTEM_INSTRUCTION.lower()
    assert "never invent" in system_lower or "do not invent" in system_lower


def test_build_prompt_contains_invention_guard():
    """build_prompt must embed the invention guard in the injected prompt text."""
    prompt = session_chat.build_prompt(
        context={"current_question": "Integrate x^2", "recent_mistakes": ["forgot +C"]},
        user_message="Am I on the right track?",
    )
    assert "do not invent" in prompt.lower() or "never invent" in prompt.lower()


def test_build_prompt_includes_current_question():
    """build_prompt must embed the current question in the user-turn prompt."""
    prompt = session_chat.build_prompt(
        context={"current_question": "Differentiate sin(2x)", "recent_mistakes": []},
        user_message="Help me with this.",
    )
    assert "Differentiate sin(2x)" in prompt


def test_build_prompt_includes_recent_mistakes():
    """build_prompt must list recent mistakes when present."""
    prompt = session_chat.build_prompt(
        context={"current_question": None, "recent_mistakes": ["sign error", "forgot +C"]},
        user_message="What did I miss?",
    )
    assert "sign error" in prompt
    assert "forgot +C" in prompt


# ── 3. build_context returns None when session not found ──────────────────────

@pytest.mark.asyncio
async def test_session_chat_returns_empty_context_for_missing_session():
    """build_context should return empty/None context when session is not in DB."""
    db = _make_db(None)

    ctx = await session_chat.build_context(db, str(uuid.uuid4()), str(uuid.uuid4()))

    assert ctx["current_question"] is None
    assert ctx["recent_mistakes"] == []
