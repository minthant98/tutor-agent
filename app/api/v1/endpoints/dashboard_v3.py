"""
app/api/v1/endpoints/dashboard_v3.py
--------------------------------------
GET /api/v1/dashboard/v3/{subject}

Dashboard v3 hero payload: narration, readiness snapshot, session plan,
total minutes, and resume state.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.redis_client import get_redis
from app.db.database import get_db
from app.db.models import LearnerSubject, Student, TutorSession
from app.services import readiness_service, today_focus_service
from app.services.marker.grader_llm import _load_student_topic_context
from app.services.narration import dashboard_narration

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Readiness thresholds required to be "at" each grade band.
BAND_THRESHOLDS: dict[str, float] = {"A*": 80, "A": 70, "B": 60, "C": 50}

# Ordered list used for fallback iteration (highest first).
_BAND_ORDER = ["A*", "A", "B", "C"]


def _band_for_grade(target_grade: str, readiness_pct: float) -> str:
    """Return the student's band relative to their target grade.

    A positive diff (≥5 pp above target threshold) → student is comfortably
    at target.  Within ±5 pp → borderline.  Below → show the band they're
    currently sitting at, or "below C".
    """
    target_pct = BAND_THRESHOLDS.get(target_grade, 60)
    diff = readiness_pct - target_pct
    if diff >= 5:
        return target_grade  # comfortably at or above target
    if diff >= -5:
        return f"{target_grade} (borderline)"
    # Below target — return the highest band whose threshold they clear
    for band in _BAND_ORDER:
        if readiness_pct >= BAND_THRESHOLDS[band]:
            return band
    return "below C"


def _band_color_index(readiness_pct: float) -> int:
    """Map raw readiness % to a 0-4 color index for the frontend.

    0 = Cool Blue (≥80), 1 = Indigo (≥65), 2 = Lavender (≥50),
    3 = Soft Gold (≥35), 4 = Amber (<35).

    The frontend reads this int directly so it never needs to string-match
    band labels.
    """
    if readiness_pct >= 80:
        return 0
    if readiness_pct >= 65:
        return 1
    if readiness_pct >= 50:
        return 2
    if readiness_pct >= 35:
        return 3
    return 4


async def _active_session_resume_state(
    db: AsyncSession, student_id, subject: str
) -> dict | None:
    """Return resume_state if there is an in-progress today-focus session."""
    row = (
        await db.execute(
            select(TutorSession)
            .where(
                TutorSession.student_id == student_id,
                TutorSession.subject == subject,
                TutorSession.ended_at.is_(None),
                TutorSession.session_type == "today_focus",
            )
            .order_by(TutorSession.started_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not row:
        return None

    plan = row.segment_plan or []
    idx = row.current_segment_idx
    # Estimate remaining minutes from the current segment onward
    remaining_minutes = sum(
        s.get("target_minutes", 8) for s in plan[idx:]
    )
    return {"segment_index": idx, "minutes_remaining": remaining_minutes}


@router.get("/v3/{subject}")
async def get_dashboard_v3(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Return full dashboard v3 hero payload."""
    # 1. Verify subject is configured for this student
    ls_row = (
        await db.execute(
            select(LearnerSubject).where(
                LearnerSubject.student_id == student.id,
                LearnerSubject.subject == subject,
                LearnerSubject.is_draft == False,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if not ls_row:
        raise HTTPException(404, "Subject not configured for this student")

    redis = get_redis()

    # 2. Today's focus plan (uses cache)
    focus = await today_focus_service.get_or_generate(db, redis, student.id, subject)
    plan = focus.get("segment_plan", [])

    # 3. Readiness
    await readiness_service.write_snapshot_if_first_today(db, student.id, subject)
    readiness_pct = await readiness_service.compute_readiness_pct(
        db, student.id, subject, ls_row.syllabus_version
    )

    # 4. Mastery trend (may be None for new students)
    trend_raw = await readiness_service.get_trend_vs_28d(db, student.id, subject)
    mastery_trend = (
        {
            "prev_mastery": round(trend_raw["prev_pct"] / 100, 3),
            "current_mastery": round(trend_raw["new_pct"] / 100, 3),
            "trend": (
                "up" if trend_raw["delta"] > 0
                else "down" if trend_raw["delta"] < 0
                else "flat"
            ),
        }
        if trend_raw
        else {"prev_mastery": 0.0, "current_mastery": 0.0, "trend": "flat"}
    )

    # 5. Real recent grades from GradedUpload rows (via grader_llm helper).
    #    Falls back to empty list if there is no plan or no topic yet.
    first_topic = plan[0].get("topic") if plan else None
    if first_topic:
        student_context = await _load_student_topic_context(
            db, student.id, subject, first_topic
        )
    else:
        student_context = {
            "recent_grades": [],
            "mastery_trend": mastery_trend,
            "recent_practice_mistakes": [],
        }

    # 6. Build narration context
    narration_ctx = {
        "recent_grades": student_context["recent_grades"],
        "mastery_trend": student_context["mastery_trend"],
        "session_plan": [
            {"intent": s.get("intent"), "topic": s.get("topic"), "why": s.get("why")}
            for s in plan
        ],
        "target_grade": ls_row.target_grade,
    }
    narration = await dashboard_narration.generate(narration_ctx)

    # 7. Resume state
    resume = await _active_session_resume_state(db, student.id, subject)

    # 8. Normalise plan segments to the v3 shape
    v3_plan = [
        {
            "intent": s.get("intent"),
            "topic": s.get("topic"),
            "why": s.get("why"),
            "minutes": s.get("target_minutes", 8),
            "questions": s.get("config", {}).get("num_questions", 3),
            "sub_skills": s.get("config", {}).get("sub_skills", []),
            "learning_objective": s.get("config", {}).get("learning_objective", ""),
        }
        for s in plan
    ]

    # 9. Readiness snapshot
    days_to_exam = (ls_row.exam_date - date.today()).days if ls_row.exam_date else None

    return {
        "narration": narration,
        "readiness_snapshot": {
            "percent": round(readiness_pct),
            "band": _band_for_grade(ls_row.target_grade, readiness_pct),
            "band_color_index": _band_color_index(readiness_pct),
            "target_grade": ls_row.target_grade,
            "days_to_exam": days_to_exam,
        },
        "session_plan": v3_plan,
        "total_minutes": sum(s["minutes"] for s in v3_plan),
        "resume_state": resume,
    }
