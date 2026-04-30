import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.endpoints.auth import get_current_student
from app.core.session_store import delete_session, load_session, save_session
from app.db.database import get_db
from app.db.models import MasteryState, Student, TutorSession
from app.schemas.schemas import (
    EndSessionResponse,
    MessageRequest,
    MessageResponse,
    ProgressResponse,
    StartSessionRequest,
    StartSessionResponse,
    TopicMastery,
)
from app.services.session_service import process_message
from app.workflows.state import SessionState, initial_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


# ── POST /sessions/start ──────────────────────────────────────────────────────

@router.post(
    "/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    body: StartSessionRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    # Free tier cannot access quiz or exam practice
    if student.subscription_tier == "free" and body.mode in ("quiz", "exam_practice"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz and exam practice require a Pro subscription.",
        )

    db_session = TutorSession(
        student_id=student.id,
        subject=body.subject,
        mode=body.mode,
    )
    db.add(db_session)
    await db.flush()

    state = initial_state(
        student_id=str(student.id),
        subject=body.subject,
        exam_board=student.exam_board,
        exam_level=student.exam_level,
        subscription_tier=student.subscription_tier,
        mode=body.mode,
    )
    state["session_id"] = str(db_session.id)

    if body.topic:
        state["topic"] = body.topic

    save_session(state)  # ← replaces: _states[state["session_id"]] = state

    return StartSessionResponse(
        session_id=state["session_id"],
        message=f"Session started! I'm your {body.subject} tutor. What would you like to work on?",
    )


# ── POST /sessions/message ────────────────────────────────────────────────────

@router.post("/message", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    state = load_session(body.session_id)  # ← replaces: _states.get(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Verify session belongs to this student
    if state["student_id"] != str(student.id):
        raise HTTPException(status_code=403, detail="Not your session.")

    result = await db.execute(
        select(TutorSession).where(TutorSession.id == body.session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session record not found.")

    response, updated_state = await process_message(
        db=db,
        db_session=db_session,
        state=state,
        student_message=body.message,
    )
    save_session(updated_state)  # ← replaces: _states[body.session_id] = updated_state

    return MessageResponse(
        session_id=body.session_id,
        response=response,
        intent=updated_state.get("intent"),
        topic=updated_state.get("topic"),
        sources_used=len(updated_state.get("retrieved_chunks", [])),
        rules_action=updated_state.get("rules_action"),
        turn_count=updated_state.get("turn_count", 0),
    )


# ── POST /sessions/end ────────────────────────────────────────────────────────

@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    state = delete_session(session_id)  # ← replaces: _states.pop(session_id, None)

    result = await db.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found.")

    from datetime import datetime, timezone
    db_session.ended_at = datetime.now(timezone.utc)
    await db.flush()

    weak = state.get("weak_topics", []) if state else []
    turns = state.get("turn_count", 0) if state else 0

    return EndSessionResponse(
        session_id=session_id,
        turns=turns,
        weak_topics=weak,
        summary=(
            f"Great session! You completed {turns} turns. "
            + (f"Topics to review: {', '.join(weak)}." if weak else "Keep it up!")
        ),
    )


# ── GET /sessions/progress ────────────────────────────────────────────────────

@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
        )
    )
    records = result.scalars().all()

    overall = (
        sum(r.mastery_score for r in records) / len(records)
        if records else 0.0
    )
    weak = [r for r in records if r.is_weak]
    strong = [r for r in records if not r.is_weak and r.mastery_score > 0.7]

    count_result = await db.execute(
        select(func.count()).select_from(TutorSession).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
        )
    )
    total_sessions = count_result.scalar() or 0

    return ProgressResponse(
        subject=subject,
        overall_mastery=round(overall, 3),
        weak_topics=[TopicMastery.model_validate(r) for r in weak],
        strong_topics=[TopicMastery.model_validate(r) for r in strong],
        total_sessions=total_sessions,
    )