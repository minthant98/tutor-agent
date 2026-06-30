import pytest
from unittest.mock import patch, AsyncMock
from app.agents import orchestrator
from app.agents.handlers import register_handler, HANDLER_REGISTRY


class _Fake:
    name = "_fake"

    async def step(self, state, db, redis, user_input):
        return {"tutor_message": "ok", "structured_cards": [], "segment_complete": True}

    async def initial_message(self, state):
        return None


@pytest.fixture(autouse=True)
def _register_fake():
    register_handler(_Fake())
    yield
    HANDLER_REGISTRY.pop("_fake", None)


@pytest.mark.asyncio
async def test_step_invokes_current_handler(db_session, redis_client, state_factory):
    state = state_factory(
        session_version=2,
        segment_plan=[
            {"idx": 0, "intent": "diagnose", "handler": "_fake", "topic": "t", "why": "", "target_minutes": 1, "status": "in_progress", "config": {}},
            {"idx": 1, "intent": "reinforce", "handler": "_fake", "topic": "t", "why": "", "target_minutes": 1, "status": "pending", "config": {}},
        ],
        current_segment_idx=0,
    )
    r = await orchestrator.step_session(state, db_session, redis_client, "")
    assert r["state_changes"]["current_segment_idx"] == 1


@pytest.mark.asyncio
async def test_last_segment_marks_session_complete(db_session, redis_client, state_factory):
    state = state_factory(
        session_version=2,
        segment_plan=[
            {"idx": 0, "intent": "diagnose", "handler": "_fake", "topic": "t", "why": "", "target_minutes": 1, "status": "in_progress", "config": {}},
        ],
        current_segment_idx=0,
    )
    r = await orchestrator.step_session(state, db_session, redis_client, "")
    assert r["session_complete"] is True


def test_shim_v1_to_v2_wraps_in_single_segment(state_factory):
    s = state_factory(session_version=1, segment_plan=[], current_segment_idx=0)
    s["subject"] = "pure_mathematics"
    s["session_phase"] = "main"
    out = orchestrator.shim_v1_to_v2(s)
    assert out["session_version"] == 2
    assert len(out["segment_plan"]) == 1
    assert out["segment_plan"][0]["handler"] == "practice"
