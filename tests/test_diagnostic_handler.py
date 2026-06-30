import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.diagnostic import DiagnosticHandler


@pytest.mark.asyncio
async def test_first_step_emits_question_card(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "diagnose", "handler": "diagnostic_question",
        "topic": "integration_basics", "why": "...", "target_minutes": 1,
        "status": "in_progress", "config": {},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.diagnostic._generate_question", new=AsyncMock(return_value={"question": "…", "mark_scheme": "…"})):
        result = await DiagnosticHandler().step(state, db_session, redis_client, user_input="")
    assert result["structured_cards"][0]["type"] == "question"
    assert result["segment_complete"] is False


@pytest.mark.asyncio
async def test_after_answer_evaluates_and_completes(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "diagnose", "handler": "diagnostic_question",
        "topic": "integration_basics", "why": "...", "target_minutes": 1,
        "status": "in_progress", "config": {"question_emitted": True, "question": "…", "mark_scheme": "…"},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.diagnostic._evaluate", new=AsyncMock(return_value={"correct": True, "marks_awarded": 1, "total_marks": 1, "feedback": "Good"})):
        result = await DiagnosticHandler().step(state, db_session, redis_client, user_input="x^2 + C")
    assert result["segment_complete"] is True
    assert result["mastery_updates"][0]["topic"] == "integration_basics"
    assert result["mastery_updates"][0]["mastery_score"] == 0.6
