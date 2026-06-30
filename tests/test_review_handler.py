import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.review import ReviewHandler


@pytest.mark.asyncio
async def test_review_pulls_recent_miss_and_emits_reframed(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "revise", "handler": "review",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress",
        "config": {"source": {"question": "Integrate x^2", "mark_scheme": "x^3/3 + C", "student_answer": "x^3"}}
    }], current_segment_idx=0)
    with patch("app.agents.handlers.review._reframe_question", new=AsyncMock(return_value={"question": "Integrate 2x", "mark_scheme": "x^2 + C"})):
        r = await ReviewHandler().step(state, db_session, redis_client, "")
    assert r["structured_cards"][0]["type"] == "question"
    assert "Integrate 2x" in r["structured_cards"][0]["data"]["question"]


@pytest.mark.asyncio
async def test_review_evaluates_and_completes(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "revise", "handler": "review",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress",
        "config": {"current_question": {"question": "Integrate 2x", "mark_scheme": "x^2 + C"}}
    }], current_segment_idx=0)
    with patch("app.agents.handlers.review._evaluate", new=AsyncMock(return_value={"correct": True, "marks_awarded": 2, "total_marks": 2})):
        r = await ReviewHandler().step(state, db_session, redis_client, "x^2 + C")
    assert r["segment_complete"] is True
