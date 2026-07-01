import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.practice import PracticeHandler


@pytest.mark.asyncio
async def test_first_step_emits_question(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": {},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._generate_question", new=AsyncMock(return_value={"question": "…", "mark_scheme": "…"})):
        r = await PracticeHandler().step(state, db_session, redis_client, "")
    assert r["structured_cards"][0]["type"] == "question"


@pytest.mark.asyncio
async def test_correct_answer_completes_segment(db_session, redis_client, state_factory):
    seg_cfg = {"questions_asked": 1, "current_question": {"question": "…", "mark_scheme": "…"}}
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": seg_cfg,
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._evaluate", new=AsyncMock(return_value={"correct": True, "marks_awarded": 3, "total_marks": 3, "feedback": "Perfect."})):
        r = await PracticeHandler().step(state, db_session, redis_client, "x^2/2 + C")
    assert r["segment_complete"] is True


@pytest.mark.asyncio
async def test_max_questions_terminates(db_session, redis_client, state_factory):
    seg_cfg = {"questions_asked": 3, "current_question": {"question": "…", "mark_scheme": "…"}}
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": seg_cfg,
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._evaluate", new=AsyncMock(return_value={"correct": False, "marks_awarded": 1, "total_marks": 3, "feedback": "Close."})):
        r = await PracticeHandler().step(state, db_session, redis_client, "wrong")
    assert r["segment_complete"] is True  # hit MAX_QUESTIONS even though wrong
