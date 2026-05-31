import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.tutor_agent import run_agent, Signal
from app.db.models import MasteryState, TutorSession
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

# Advance phase at these turn counts (turn = number of student messages sent so far)
_PHASE_SCHEDULE: dict[int, str] = {
    0: "intro",       # Alex: hi + what do you want to work on?
    1: "diagnostic",  # Alex: acknowledge topic, calibration question
    3: "warmup",      # Alex: easy question on their topic
    5: "main",        # Alex: full practice at appropriate difficulty
}


def _advance_phase(state: SessionState) -> None:
    turn = state.get("turn_count", 0)
    new_phase = _PHASE_SCHEDULE.get(turn)
    if new_phase and state.get("session_phase") != new_phase:
        state["session_phase"] = new_phase
        logger.info("Phase → %s (turn %d)", new_phase, turn)


async def stream_response(
    db: AsyncSession,
    db_session: TutorSession,
    state: SessionState,
    student_message: str,
    signal: Signal = None,
) -> AsyncGenerator[str, None]:
    """
    Run one agent turn. Yields response tokens for SSE streaming.
    Handles all state mutation, DB mastery sync, and session persistence
    after the final token is yielded.
    """
    state["current_input"] = student_message
    state["conversation_history"].append({
        "role": "student",
        "content": student_message,
        "metadata": {"turn": state.get("turn_count", 0)},
    })

    # Capture what the student wants to work on from their very first reply
    if state.get("turn_count", 0) == 0 and not state.get("session_goal"):
        state["session_goal"] = student_message[:300]

    _advance_phase(state)

    response_parts: list[str] = []
    async for token in run_agent(state, signal):
        response_parts.append(token)
        yield token

    response_text = "".join(response_parts)
    state["conversation_history"].append({
        "role": "tutor",
        "content": response_text,
        "metadata": {"turn": state.get("turn_count", 0)},
    })
    state["turn_count"] = state.get("turn_count", 0) + 1

    # Sync mastery to DB if an evaluation happened this turn
    if state.get("pending_mastery"):
        await _update_mastery(db, state)
        state["pending_mastery"] = None

    db_session.messages = state["conversation_history"]
    db_session.topic = state.get("session_goal")
    await db.flush()


async def _update_mastery(db: AsyncSession, state: SessionState) -> None:
    pending = state.get("pending_mastery")
    if not pending:
        return

    topic = pending["topic"]
    score = float(pending["score"])
    student_id = state["student_id"]

    stmt = select(MasteryState).where(
        MasteryState.student_id == student_id,
        MasteryState.subject == state["subject"],
        MasteryState.topic == topic,
    )
    result = await db.execute(stmt)
    mastery = result.scalar_one_or_none()

    if mastery is None:
        mastery = MasteryState(
            student_id=student_id,
            subject=state["subject"],
            topic=topic,
            mastery_score=0.0,
            total_attempts=0,
            correct_streak=0,
            is_weak=False,
        )
        db.add(mastery)

    current_score = float(mastery.mastery_score or 0.0)
    current_streak = int(mastery.correct_streak or 0)

    alpha = 0.3
    mastery.mastery_score = alpha * score + (1 - alpha) * current_score
    mastery.total_attempts = int(mastery.total_attempts or 0) + 1
    mastery.last_reviewed_at = datetime.now(timezone.utc)
    mastery.correct_streak = current_streak + 1 if score >= 0.6 else 0
    mastery.is_weak = mastery.mastery_score < 0.5

    await db.flush()
    logger.info("Mastery: topic=%s score=%.2f ema=%.2f", topic, score, mastery.mastery_score)
