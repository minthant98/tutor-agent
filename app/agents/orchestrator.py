"""
Segment-based session orchestrator (Phase C).

step_session() is the new entry point for processing a user turn.
session_service.stream_response() calls this instead of run_agent().
"""
import logging
from app.agents.handlers import HANDLER_REGISTRY
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)


def shim_v1_to_v2(state: SessionState) -> SessionState:
    """Wrap a legacy v1 session in a single-segment v2 plan at load time.

    Sessions created before the segment engine (session_version=1 or missing)
    are transparently promoted to v2 so the orchestrator can handle them
    without a DB migration of in-flight sessions.
    """
    if state.get("session_version") == 2:
        return state
    state["session_version"] = 2
    state["session_type"] = state.get("session_type") or "practice"
    if not state.get("segment_plan"):
        state["segment_plan"] = [{
            "idx": 0,
            "intent": "reinforce",
            "handler": "practice",
            "topic": None,
            "why": "Legacy session wrapped by shim_v1_to_v2",
            "target_minutes": 15,
            "status": "in_progress",
            "config": {},
        }]
    state.setdefault("current_segment_idx", 0)
    state.setdefault("segment_progress", {})
    return state


async def step_session(state: SessionState, db, redis, user_input: str) -> dict:
    """Process one user turn through the segment-based engine.

    Returns:
        {
          tutor_message: str | None,
          structured_cards: list[dict],
          mastery_updates: list[dict],
          state_changes: dict,        # caller must apply to state + DB
          session_complete: bool,
        }
    """
    state = shim_v1_to_v2(state)
    plan = state["segment_plan"]
    idx = state["current_segment_idx"]

    if idx >= len(plan):
        # All segments already done — session is complete
        return {
            "tutor_message": "Great work today — session complete.",
            "structured_cards": [],
            "mastery_updates": [],
            "state_changes": {"session_complete": True},
            "session_complete": True,
        }

    seg = plan[idx]
    handler = HANDLER_REGISTRY.get(seg["handler"])
    if handler is None:
        logger.error("Unknown handler: %s", seg["handler"])
        return {
            "tutor_message": "We hit a snag — please retry.",
            "structured_cards": [],
            "mastery_updates": [],
            "state_changes": {},
            "session_complete": False,
            "error": f"unknown handler {seg['handler']}",
        }

    try:
        from app.core.telemetry import capture
        capture(str(state.get("student_id", "")), "segment_started", {
            "intent": seg.get("intent"),
            "handler": seg.get("handler"),
            "topic": seg.get("topic"),
            "target_minutes": seg.get("target_minutes"),
            "segment_idx": idx,
        })
    except Exception:
        pass

    result = await handler.step(state, db, redis, user_input)
    state_changes: dict = {}
    # The segment plan list is mutated in-place by the handler (via cfg dict).
    # Include it in state_changes so session_service persists it.
    state_changes["segment_plan"] = plan

    session_complete = False
    if result.get("segment_complete"):
        seg["status"] = "done"
        try:
            from app.core.telemetry import capture
            capture(str(state.get("student_id", "")), "segment_completed", {
                "intent": seg.get("intent"),
                "handler": seg.get("handler"),
                "topic": seg.get("topic"),
                "target_minutes": seg.get("target_minutes"),
                "segment_idx": idx,
                "outcome": "completed",
            })
        except Exception:
            pass
        next_idx = idx + 1
        if next_idx < len(plan):
            plan[next_idx]["status"] = "in_progress"
            state_changes["current_segment_idx"] = next_idx
            # Add transition message from handler.initial_message if available
            next_handler = HANDLER_REGISTRY.get(plan[next_idx]["handler"])
            opener = None
            if next_handler is not None:
                try:
                    opener = await next_handler.initial_message(state)
                except Exception:
                    pass
            transition = f"Nice work — let's move on to your {plan[next_idx]['intent']} segment."
            tutor_msg = (result.get("tutor_message") or "").strip()
            result["tutor_message"] = (
                (tutor_msg + "\n\n" if tutor_msg else "") +
                transition +
                (("\n\n" + opener) if opener else "")
            ).strip()
        else:
            state_changes["session_complete"] = True
            session_complete = True

    return {
        "tutor_message": result.get("tutor_message"),
        "structured_cards": result.get("structured_cards", []),
        "mastery_updates": result.get("mastery_updates", []),
        "state_changes": state_changes,
        "session_complete": session_complete,
    }
