"""
app/api/v1/endpoints/dashboard.py
-----------------------------------
GET /api/v1/dashboard/{subject} — dashboard payload for a single subject.

Returns readiness, today's focus plan, resume session, recent activity,
strong/weak topics, and subject switcher options — all in one round-trip.
"""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.grade_prediction import predict_grade
from app.core.redis_client import get_redis
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, Student, SyllabusTopic, TutorSession
from app.schemas.dashboard import (
    DashboardPayload,
    RecentActivityOut,
    ResumeSessionOut,
    SegmentOut,
    TodayFocusOut,
    TopicMastery,
    TrendOut,
)
from app.services import readiness_service, today_focus_service
from app.services.learner_profile_service import is_supported_combo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{subject}", response_model=DashboardPayload)
async def get_dashboard(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Return the full dashboard payload for one subject."""
    # 1. Verify student has this subject configured (non-draft)
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

    # 2. Verify the combo is currently supported
    if not is_supported_combo(ls_row.subject, ls_row.exam_board, ls_row.exam_level):
        raise HTTPException(404, "Subject not yet supported")

    redis = get_redis()

    # ── Stale-session auto-close ───────────────────────────────────────────────
    # Practice modes: 1h window. Today's Focus + diagnostic: 24h window.
    PRACTICE_MODES = ("quick_practice", "weak_areas", "drill_in")

    now = datetime.now(timezone.utc)
    practice_cutoff = now - timedelta(hours=1)
    default_cutoff = now - timedelta(hours=24)

    stale_rows = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
            TutorSession.ended_at.is_(None),
        )
    )).scalars().all()

    for s in stale_rows:
        if s.session_type in PRACTICE_MODES:
            if s.started_at and s.started_at < practice_cutoff:
                s.ended_at = s.started_at + timedelta(hours=1)
        else:
            if s.started_at and s.started_at < default_cutoff:
                s.ended_at = s.started_at + timedelta(hours=24)
    await db.flush()

    # 3. Readiness
    await readiness_service.write_snapshot_if_first_today(db, student.id, subject)
    readiness_pct = await readiness_service.compute_readiness_pct(
        db, student.id, subject, ls_row.syllabus_version
    )
    trend_raw = await readiness_service.get_trend_vs_28d(db, student.id, subject)

    # 4. Today's focus
    today_focus = await today_focus_service.get_or_generate(db, redis, student.id, subject)

    # 5. Resume session detection (active Today's Focus / diagnostic only — practice modes excluded)
    rs_row = (
        await db.execute(
            select(TutorSession)
            .where(
                TutorSession.student_id == student.id,
                TutorSession.subject == subject,
                TutorSession.ended_at.is_(None),
                TutorSession.session_type.in_(["practice", "diagnostic"]),
            )
            .order_by(TutorSession.started_at.desc())
        )
    ).scalars().first()

    resume = None
    if rs_row and rs_row.started_at:
        plan = rs_row.segment_plan or []
        if rs_row.current_segment_idx < len(plan):
            resume = ResumeSessionOut(
                session_id=str(rs_row.id),
                completed_segments=rs_row.current_segment_idx,
                total_segments=len(plan),
            )

    # 6. Strong / weak topics from mastery state
    mastery_rows = (
        await db.execute(
            select(MasteryState.topic, MasteryState.mastery_score).where(
                MasteryState.student_id == student.id,
                MasteryState.subject == subject,
            )
        )
    ).all()
    topic_name_map = dict(
        (
            await db.execute(
                select(SyllabusTopic.topic_id, SyllabusTopic.topic_name).where(
                    SyllabusTopic.subject == subject,
                    SyllabusTopic.version == ls_row.syllabus_version,
                )
            )
        ).all()
    )

    def _tm(topic_id: str, score) -> TopicMastery:
        return TopicMastery(
            topic=topic_id,
            topic_name=topic_name_map.get(topic_id, topic_id),
            mastery_pct=int((score or 0) * 100),
        )

    sorted_asc = sorted(mastery_rows, key=lambda r: r[1] or 0)
    sorted_desc = sorted(mastery_rows, key=lambda r: -(r[1] or 0))
    weak_topics = [_tm(t, s) for t, s in sorted_asc[:3]]
    strong_topics = [_tm(t, s) for t, s in sorted_desc[:3]]

    # 7. Recent activity (last completed session)
    last_session = (
        await db.execute(
            select(TutorSession)
            .where(
                TutorSession.student_id == student.id,
                TutorSession.subject == subject,
                TutorSession.ended_at.is_not(None),
            )
            .order_by(TutorSession.ended_at.desc())
            .limit(1)
        )
    ).scalars().first()

    recent_activity = None
    if last_session and last_session.ended_at:
        days_ago = (date.today() - last_session.ended_at.date()).days
        recent_activity = RecentActivityOut(
            last_studied=last_session.ended_at.date(),
            summary=last_session.topic or "Session",
            cold=days_ago >= 3,
        )

    # 8. Subject switcher — all non-draft subjects for this student
    all_subjects = list(
        (
            await db.execute(
                select(LearnerSubject.subject).where(
                    LearnerSubject.student_id == student.id,
                    LearnerSubject.is_draft == False,  # noqa: E712
                )
            )
        ).scalars().all()
    )

    # 9. Assemble and return
    plan_out = [SegmentOut(**s) for s in today_focus["segment_plan"]]
    return DashboardPayload(
        subject=subject,
        exam_date=ls_row.exam_date,
        days_until_exam=(ls_row.exam_date - date.today()).days if ls_row.exam_date else None,
        target_grade=ls_row.target_grade,
        predicted_grade=predict_grade(readiness_pct),
        readiness_pct=readiness_pct,
        readiness_trend=TrendOut(**trend_raw) if trend_raw else None,
        today_focus=TodayFocusOut(
            shape=today_focus["shape"],
            segment_plan=plan_out,
            total_minutes=sum(s.target_minutes for s in plan_out),
            generated_at=today_focus["generated_at"],
        ),
        resume_session=resume,
        recent_activity=recent_activity,
        strong_topics=strong_topics,
        weak_topics=weak_topics,
        subject_options=all_subjects,
    )
