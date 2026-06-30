import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, AsyncGenerator, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents import orchestrator
from app.agents.tutor_agent import Signal
from app.core.telemetry import capture
from app.db.models import MasteryState, TutorSession
from app.workflows.state import SessionState, initial_state

if TYPE_CHECKING:
    from app.db.models import Student

logger = logging.getLogger(__name__)


async def stream_response(
    db: AsyncSession,
    db_session: TutorSession,
    state: SessionState,
    student_message: str,
    signal: Signal = None,
) -> AsyncGenerator[str, None]:
    """
    Run one agent turn via the segment orchestrator.
    Yields response tokens for SSE streaming.
    Handles all state mutation, DB mastery sync, and session persistence.
    """
    state["current_input"] = student_message
    state["conversation_history"].append({
        "role": "student",
        "content": student_message,
        "metadata": {"turn": state.get("turn_count", 0)},
    })

    # Capture session goal from the very first reply
    if state.get("turn_count", 0) == 0 and not state.get("session_goal"):
        state["session_goal"] = student_message[:300]

    # --- Segment engine turn ---
    result = await orchestrator.step_session(state, db, None, student_message)

    tutor_message = result.get("tutor_message") or ""
    mastery_updates = result.get("mastery_updates", [])
    state_changes = result.get("state_changes", {})
    session_complete = result.get("session_complete", False)

    # Stash structured_cards in state so the endpoint can emit them as SSE events.
    # The endpoint clears this field after reading it each turn.
    state["structured_cards"] = result.get("structured_cards", [])

    # Apply state_changes from orchestrator
    for key, value in state_changes.items():
        state[key] = value  # type: ignore[literal-required]

    # Stream the tutor message token by token (chunk into words for smooth SSE)
    for word in tutor_message.split(" "):
        chunk = word + " "
        yield chunk

    state["conversation_history"].append({
        "role": "tutor",
        "content": tutor_message,
        "metadata": {"turn": state.get("turn_count", 0)},
    })
    state["turn_count"] = state.get("turn_count", 0) + 1

    # Sync mastery to DB for all mastery_updates from this turn
    for update in mastery_updates:
        await _apply_mastery_update(db, state, update)

    # Handle session completion
    if session_complete:
        db_session.ended_at = datetime.now(timezone.utc)
        # Invalidate today's focus cache so tomorrow regenerates fresh
        try:
            from app.services.today_focus_service import invalidate_today
            from app.core.redis_client import get_redis
            _redis = get_redis()
            invalidate_today(_redis, state["student_id"], state["subject"])
        except (ImportError, Exception) as _e:
            logger.debug("today_focus_service.invalidate_today not available: %s", _e)
        capture(state["student_id"], "session_complete", {
            "subject": state.get("subject"),
            "turn_count": state.get("turn_count"),
            "segment_count": len(state.get("segment_plan", [])),
        })

    db_session.messages = state["conversation_history"]
    db_session.topic = state.get("session_goal")
    await db.flush()


async def _apply_mastery_update(db: AsyncSession, state: SessionState, update: dict) -> None:
    """Apply a single mastery update dict (from a handler's mastery_updates list) to DB."""
    topic = update.get("topic")
    if not topic:
        return

    student_id = state["student_id"]
    subject = state["subject"]

    stmt = select(MasteryState).where(
        MasteryState.student_id == student_id,
        MasteryState.subject == subject,
        MasteryState.topic == topic,
    )
    result = await db.execute(stmt)
    mastery = result.scalar_one_or_none()

    if mastery is None:
        mastery = MasteryState(
            student_id=student_id,
            subject=subject,
            topic=topic,
            mastery_score=0.0,
            total_attempts=0,
            correct_streak=0,
            is_weak=False,
        )
        db.add(mastery)

    current_score = float(mastery.mastery_score or 0.0)
    current_streak = int(mastery.correct_streak or 0)

    # Handlers use either absolute mastery_score or delta (mastery_score_delta)
    if "mastery_score" in update:
        # Absolute score from diagnostic handler (e.g., 0.6 or 0.2)
        new_score = float(update["mastery_score"])
        alpha = 0.3
        mastery.mastery_score = alpha * new_score + (1 - alpha) * current_score
    elif "mastery_score_delta" in update:
        # Delta from practice/review handlers
        delta = float(update["mastery_score_delta"])
        mastery.mastery_score = max(0.0, min(1.0, current_score + delta))

    correct_delta = int(update.get("correct_delta", 0))
    attempt_delta = int(update.get("attempt_delta", 1))
    mastery.total_attempts = int(mastery.total_attempts or 0) + attempt_delta
    mastery.last_reviewed_at = datetime.now(timezone.utc)
    mastery.correct_streak = current_streak + correct_delta if correct_delta > 0 else 0
    mastery.is_weak = mastery.mastery_score < 0.5

    await db.flush()
    logger.info("Mastery: topic=%s score=%.2f", topic, mastery.mastery_score)


async def _regenerate_plan(student_id: str, subject: str) -> None:
    """Fire-and-forget: regenerate study plan when needed."""
    try:
        from app.db.database import AsyncSessionLocal
        from app.services.study_plan_service import generate_plan
        from app.db.models import Student, StudyPlan
        async with AsyncSessionLocal() as db:
            student = await db.get(Student, student_id)
            if not student:
                return
            result = await db.execute(
                select(StudyPlan).where(
                    StudyPlan.student_id == student.id,
                    StudyPlan.subject == subject,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                await db.delete(existing)
                await db.flush()
            wt_result = await db.execute(
                select(MasteryState.topic).where(
                    MasteryState.student_id == student.id,
                    MasteryState.subject == subject,
                    MasteryState.is_weak == True,
                )
            )
            weak_topics = [r for r in wt_result.scalars()]
            plan_data = await generate_plan(
                subject=subject,
                exam_board=student.exam_board,
                exam_date=student.exam_date,
                weak_topics=weak_topics,
            )
            from app.services.study_plan_service import _weeks_until
            db.add(StudyPlan(
                student_id=student.id,
                subject=subject,
                weeks_remaining=_weeks_until(student.exam_date),
                plan=plan_data,
            ))
            await db.commit()
            logger.info("Study plan regenerated for student %s", student_id)
    except Exception as e:
        logger.warning("Background plan regeneration failed: %s", e)


def _rebuild_resume_state(
    session_id: str,
    student: "Student",
    db_session: TutorSession,
    messages: list,
    weak_topics: list[str],
) -> SessionState:
    """Pure helper: rebuild Redis state from DB rows on session resume.

    Extracted from the resume_session endpoint so it can be unit-tested
    without HTTP context (no FastAPI auth imports).
    """
    turn_count = len([m for m in messages if m.get("role") == "student"])

    # Determine phase from turn count
    if turn_count >= 4:
        phase = "main"
    elif turn_count >= 2:
        phase = "warmup"
    elif turn_count >= 1:
        phase = "diagnostic"
    else:
        phase = "intro"

    state = initial_state(
        student_id=str(student.id),
        subject=db_session.subject,
        exam_board=student.exam_board,
        exam_level=student.exam_level,
        subscription_tier=student.subscription_tier,
        exam_date=str(student.exam_date) if student.exam_date else None,
        weak_topics=weak_topics,
    )
    state["session_id"] = session_id
    state["conversation_history"] = messages
    state["turn_count"] = turn_count
    state["session_phase"] = phase
    state["session_goal"] = db_session.topic
    # Restore persisted session structure so the segment engine resumes correctly.
    state["preferences"] = student.preferences or {}
    state["session_type"] = db_session.session_type
    state["session_version"] = db_session.session_version
    state["segment_plan"] = db_session.segment_plan or []
    state["current_segment_idx"] = db_session.current_segment_idx
    return state
