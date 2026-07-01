import os
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Student, LearnerSubject, MasteryState, TutorSession, TodayFocusHistory
from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.schemas.admin import InspectStudentResponse

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


def require_admin(student: Student = Depends(get_current_student)) -> Student:
    """Dependency that ensures the current student is an admin."""
    if not student.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return student


@router.get("/students/{student_id}/inspect", response_model=InspectStudentResponse)
async def inspect_student(
    student_id: str,
    admin: Student = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Inspect a student's complete profile (learner data, subjects, mastery, sessions).
    Requires admin authorization.
    """
    # Fetch target student
    target = await db.get(Student, UUID(student_id))
    if not target:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch subjects
    subjects = (
        await db.execute(
            select(LearnerSubject).where(LearnerSubject.student_id == target.id)
        )
    ).scalars().all()

    # Fetch mastery states
    mastery = (
        await db.execute(
            select(MasteryState).where(MasteryState.student_id == target.id)
        )
    ).scalars().all()

    # Fetch latest today_focus
    latest_focus = (
        await db.execute(
            select(TodayFocusHistory)
            .where(TodayFocusHistory.student_id == target.id)
            .order_by(TodayFocusHistory.focus_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Fetch active session (no ended_at)
    active = (
        await db.execute(
            select(TutorSession)
            .where(
                TutorSession.student_id == target.id,
                TutorSession.ended_at.is_(None),
            )
            .order_by(TutorSession.started_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Fetch recent sessions (last 7)
    recent_sessions = (
        await db.execute(
            select(TutorSession)
            .where(TutorSession.student_id == target.id)
            .order_by(TutorSession.started_at.desc())
            .limit(7)
        )
    ).scalars().all()

    return InspectStudentResponse.model_validate({
        "profile": {
            "id": str(target.id),
            "name": target.name,
            "email": target.email,
            "onboarded_at": target.onboarded_at,
            "subscription_tier": target.subscription_tier,
            "preferences": target.preferences or {},
        },
        "subjects": [
            {
                "id": str(s.id),
                "subject": s.subject,
                "exam_board": s.exam_board,
                "exam_date": s.exam_date,
                "target_grade": s.target_grade,
                "syllabus_version": s.syllabus_version,
                "is_draft": s.is_draft,
            }
            for s in subjects
        ],
        "mastery": [
            {
                "topic": m.topic,
                "mastery_score": m.mastery_score,
                "total_attempts": m.total_attempts,
                "is_weak": m.is_weak,
            }
            for m in mastery
        ],
        "latest_today_focus": {
            "focus_date": latest_focus.focus_date,
            "shape": latest_focus.shape,
            "segment_plan": latest_focus.segment_plan,
            "reasoning": latest_focus.reasoning,
        }
        if latest_focus
        else None,
        "active_session": {
            "id": str(active.id),
            "session_type": active.session_type,
            "session_version": active.session_version,
            "segment_plan": active.segment_plan,
            "current_segment_idx": active.current_segment_idx,
            "started_at": active.started_at,
        }
        if active
        else None,
        "recent_sessions": [
            {
                "id": str(s.id),
                "subject": s.subject,
                "topic": s.topic,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "session_type": s.session_type,
            }
            for s in recent_sessions
        ],
    })


@router.post("/ingest")
async def trigger_ingestion(secret: str):
    if secret != ADMIN_SECRET or not ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    from app.rag.ingestor import KnowledgeIngestor
    import asyncio

    ingestor = KnowledgeIngestor()
    collection = ingestor.get_or_create_collection(
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    # Ingest sample content to verify it works
    sample = """
    Integration by Parts
    The formula is: ∫u dv = uv - ∫v du
    Use the LIATE rule to choose u:
    L: Logarithmic, I: Inverse trig, A: Algebraic, T: Trig, E: Exponential

    Example: ∫x eˣ dx
    Let u = x, dv = eˣ dx
    du = dx, v = eˣ
    ∫x eˣ dx = x eˣ - ∫eˣ dx = x eˣ - eˣ + C = eˣ(x-1) + C

    The Chain Rule
    If y = f(g(x)), then dy/dx = f'(g(x)) · g'(x)

    The Product Rule
    If y = uv, then dy/dx = u(dv/dx) + v(du/dx)

    Differentiation from First Principles
    f'(x) = lim(h→0) [f(x+h) - f(x)] / h
    """

    n = ingestor.ingest_text(
        text=sample,
        metadata={
            "subject": "pure_mathematics",
            "exam_board": "edexcel",
            "exam_level": "a_level",
            "doc_type": "syllabus",
            "source_file": "sample_content.txt",
        },
        collection=collection,
    )

    return {
        "chunks_added": n,
        "total_chunks": collection.count(),
    }