import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.tutor_agent import run_agent, Signal
from app.core.telemetry import capture
from app.db.models import MasteryState, TutorSession
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

# Phase advances AFTER Alex responds, keyed on the completed turn count.
_PHASE_SCHEDULE: dict[int, str] = {
    0:  "diagnostic",    # after intro: student stated topic → calibrate
    2:  "warmup",        # after calibration → easy question
    4:  "main",          # after warmup → full practice
    10: "consolidation", # after ~6 main exchanges → wrap up + study plan
}


def _advance_phase(state: SessionState) -> bool:
    """Called after a turn completes. Returns True if phase just became consolidation."""
    completed = state.get("turn_count", 0)
    new_phase = _PHASE_SCHEDULE.get(completed)
    if new_phase and state.get("session_phase") != new_phase:
        prev_phase = state.get("session_phase")
        state["session_phase"] = new_phase
        logger.info("Phase → %s (after turn %d)", new_phase, completed)
        capture(state["student_id"], "phase_advanced", {
            "from": prev_phase,
            "to": new_phase,
            "turn_count": completed,
            "subject": state.get("subject"),
        })
        return new_phase == "consolidation"
    return False


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
    entered_consolidation = _advance_phase(state)

    # Sync mastery to DB if an evaluation happened this turn
    if state.get("pending_mastery"):
        await _update_mastery(db, state)
        state["pending_mastery"] = None

    # Auto-regenerate study plan when consolidation starts
    if entered_consolidation:
        asyncio.create_task(_regenerate_plan(state["student_id"], state["subject"]))
        state["plan_ready"] = True

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


async def _regenerate_plan(student_id: str, subject: str) -> None:
    """Fire-and-forget: regenerate study plan after consolidation starts."""
    try:
        from app.db.database import AsyncSessionLocal
        from app.services.study_plan_service import generate_plan
        from app.db.models import Student, StudyPlan
        async with AsyncSessionLocal() as db:
            student = await db.get(Student, student_id)
            if not student:
                return
            # Remove existing plan for this subject
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
            # Fetch weak topics from mastery state
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
            logger.info("Study plan regenerated for student %s after consolidation", student_id)
    except Exception as e:
        logger.warning("Background plan regeneration failed: %s", e)
