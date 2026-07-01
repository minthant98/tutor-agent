import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.endpoints.auth import get_current_student
from app.core.dependencies import check_message_limit
from app.core.session_store import delete_session, load_session, save_session
from app.db.database import get_db
from app.db.models import MasteryState, Student, TutorSession
from app.schemas.schemas import (
    ActiveSessionResponse,
    EndSessionResponse,
    MessageRequest,
    MessageResponse,
    ProgressResponse,
    StartSessionRequest,
    StartSessionResponse,
    TopicMastery,
)
from app.agents.tutor_agent import generate_opening_message
from app.services.session_service import stream_response, _rebuild_resume_state
from app.workflows.state import SessionState, initial_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _load_weak_topics(db: AsyncSession, student_id: str, subject: str) -> list[str]:
    """Load weak topics from DB mastery records for returning students."""
    result = await db.execute(
        select(MasteryState.topic).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.is_weak == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


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
    # Build diagnostic segment plan if requested
    diagnostic_plan: list[dict] = []
    if body.session_type == "diagnostic":
        from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
        diagnostic_plan = [
            {
                "idx": i,
                "intent": "diagnose",
                "handler": "diagnostic_question",
                "topic": t["topic_id"],
                "topic_name": t["topic_name"],
                "why": "Baseline diagnostic",
                "target_minutes": 2,
                "status": "in_progress" if i == 0 else "pending",
                "config": {},
            }
            for i, t in enumerate(EDEXCEL_9MA0_TOPICS[:7])
        ]

    # Use provided segment_plan or the diagnostic plan
    resolved_plan = body.segment_plan or (diagnostic_plan if body.session_type == "diagnostic" else [])

    db_session = TutorSession(
        student_id=student.id,
        subject=body.subject,
        mode="explain",
        session_type=body.session_type,
        segment_plan=resolved_plan,
    )
    db.add(db_session)
    await db.flush()

    weak_topics = await _load_weak_topics(db, str(student.id), body.subject)

    state = initial_state(
        student_id=str(student.id),
        subject=body.subject,
        exam_board=student.exam_board,
        exam_level=student.exam_level,
        subscription_tier=student.subscription_tier,
        exam_date=body.exam_date,
        weak_topics=weak_topics,
    )
    state["session_id"] = str(db_session.id)

    if body.topic:
        state["session_goal"] = body.topic

    opening = await generate_opening_message(state)

    # Build conversation history seed
    history: list[dict] = []

    # Store return_to as system metadata (for session-end handler)
    if body.return_to:
        history.append({
            "role": "system",
            "content": f"return_to:{body.return_to}",
        })

    history.append({
        "role": "tutor",
        "content": opening,
        "metadata": {"turn": 0, "type": "opening"},
    })

    state["conversation_history"].extend(history)

    save_session(state)
    await db.commit()

    from app.core.telemetry import capture
    capture(str(student.id), "session_started", {
        "session_id": state["session_id"],
        "subject": body.subject,
        "exam_board": student.exam_board,
        "is_new_student": not bool(weak_topics),
        "subscription_tier": student.subscription_tier,
    })

    return StartSessionResponse(
        session_id=state["session_id"],
        message=opening,
        is_new_student=not bool(weak_topics),
    )


# ── POST /sessions/stream (SSE) ───────────────────────────────────────────────

@router.post("/stream")
async def stream_message(
    body: MessageRequest,
    student: Student = Depends(check_message_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Server-sent events endpoint. Streams response tokens as they are generated.

    Client reads:
      data: {"token": "..."}        — one or more per response
      data: {"done": true, ...}     — final event with session metadata
      data: {"error": "..."}        — on failure
    """
    state = load_session(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")
    if state["student_id"] != str(student.id):
        raise HTTPException(status_code=403, detail="Not your session.")

    result = await db.execute(
        select(TutorSession).where(TutorSession.id == body.session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session record not found.")

    async def generate():
        try:
            async for token in stream_response(
                db=db,
                db_session=db_session,
                state=state,
                student_message=body.message,
                signal=body.signal,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Emit structured cards produced by the orchestrator this turn, then clear.
            # structured_cards is a list of dicts with a "type" field (e.g. "question", "evaluation").
            for card in state.get("structured_cards") or []:
                yield f"data: {json.dumps({'card': card})}\n\n"
            state["structured_cards"] = []

            save_session(state)
            await db.commit()

            yield f"data: {json.dumps({'done': True, 'session_phase': state.get('session_phase'), 'weak_topics': state.get('weak_topics', []), 'turn_count': state.get('turn_count', 0), 'plan_ready': state.get('plan_ready', False)})}\n\n"

        except Exception as e:
            logger.error("Stream error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'error': 'Something went wrong. Please try again.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /sessions/message (non-streaming, for testing) ──────────────────────

@router.post("/message", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    student: Student = Depends(check_message_limit),
    db: AsyncSession = Depends(get_db),
):
    state = load_session(body.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")
    if state["student_id"] != str(student.id):
        raise HTTPException(status_code=403, detail="Not your session.")

    result = await db.execute(
        select(TutorSession).where(TutorSession.id == body.session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session record not found.")

    response_parts: list[str] = []
    async for token in stream_response(
        db=db,
        db_session=db_session,
        state=state,
        student_message=body.message,
        signal=body.signal,
    ):
        response_parts.append(token)

    save_session(state)
    await db.commit()

    return MessageResponse(
        session_id=body.session_id,
        response="".join(response_parts),
        session_phase=state.get("session_phase", "diagnostic"),
        weak_topics=state.get("weak_topics", []),
        turn_count=state.get("turn_count", 0),
    )


# ── POST /sessions/end ────────────────────────────────────────────────────────

@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    state = delete_session(session_id)

    result = await db.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found.")

    from datetime import datetime, timezone
    db_session.ended_at = datetime.now(timezone.utc)
    await db.commit()

    weak = state.get("weak_topics", []) if state else []
    turns = state.get("turn_count", 0) if state else 0

    from app.core.telemetry import capture
    capture(str(student.id), "session_ended", {
        "session_id": session_id,
        "turn_count": turns,
        "weak_topic_count": len(weak),
        "subject": db_session.subject,
        "final_phase": (state.get("session_phase") if state else None),
        "reached_consolidation": ((state.get("session_phase") if state else None) == "consolidation"),
    })

    return EndSessionResponse(
        session_id=session_id,
        turns=turns,
        weak_topics=weak,
        summary=(
            f"Great session! You completed {turns} turns. "
            + (f"Topics to review: {', '.join(weak)}." if weak else "Keep it up!")
        ),
    )


# ── GET /sessions/active ─────────────────────────────────────────────────────

@router.get("/active", response_model=ActiveSessionResponse | None)
async def get_active_session(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent unended session, or null if none."""
    result = await db.execute(
        select(TutorSession)
        .where(TutorSession.student_id == student.id, TutorSession.ended_at.is_(None))
        .order_by(TutorSession.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None

    messages = session.messages or []
    tutor_messages = [m for m in messages if m.get("role") == "tutor"]
    last_message = tutor_messages[-1]["content"][:120] if tutor_messages else None

    return ActiveSessionResponse(
        session_id=str(session.id),
        subject=session.subject,
        topic=session.topic,
        started_at=session.started_at,
        message_count=len([m for m in messages if m.get("role") == "student"]),
        last_message=last_message,
        segment_plan=session.segment_plan or [],
        current_segment_idx=session.current_segment_idx or 0,
    )


# ── POST /sessions/resume ─────────────────────────────────────────────────────

@router.post("/resume/{session_id}", response_model=StartSessionResponse)
async def resume_session(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Rebuild Redis state from DB and return the last tutor message to resume from."""
    result = await db.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )
    db_session = result.scalar_one_or_none()
    if not db_session or str(db_session.student_id) != str(student.id):
        raise HTTPException(status_code=404, detail="Session not found.")

    messages = db_session.messages or []
    weak_topics = await _load_weak_topics(db, str(student.id), db_session.subject)

    state = _rebuild_resume_state(session_id, student, db_session, messages, weak_topics)

    save_session(state)

    tutor_messages = [m for m in messages if m.get("role") == "tutor"]
    last_message = tutor_messages[-1]["content"] if tutor_messages else "Welcome back! Where were we?"

    from app.core.telemetry import capture
    capture(str(student.id), "session_resumed", {
        "session_id": session_id,
        "subject": db_session.subject,
        "turn_count": state["turn_count"],
        "phase": state["session_phase"],
    })

    return StartSessionResponse(
        session_id=session_id,
        message=last_message,
        is_new_student=False,
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
