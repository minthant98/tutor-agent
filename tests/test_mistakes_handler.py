import pytest
from app.agents.handlers.mistakes import MistakesHandler


@pytest.mark.asyncio
async def test_mistakes_walks_each_collected_item(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "consolidate", "handler": "mistakes",
        "topic": None, "why": "...", "target_minutes": 5,
        "status": "in_progress",
        "config": {"mistakes": [
            {"question": "Q1", "mark_scheme": "MS1", "student_answer": "wrong1"},
            {"question": "Q2", "mark_scheme": "MS2", "student_answer": "wrong2"},
        ]}
    }], current_segment_idx=0)
    # Step 1: emit first correction
    r = await MistakesHandler().step(state, db_session, redis_client, "")
    assert r["segment_complete"] is False
    assert "Q1" in r["tutor_message"]


@pytest.mark.asyncio
async def test_mistakes_completes_when_list_exhausted(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "consolidate", "handler": "mistakes",
        "topic": None, "why": "...", "target_minutes": 5,
        "status": "in_progress",
        "config": {"mistakes": [], "idx": 0}
    }], current_segment_idx=0)
    r = await MistakesHandler().step(state, db_session, redis_client, "ok")
    assert r["segment_complete"] is True
