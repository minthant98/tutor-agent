"""
app/api/v1/endpoints/progress.py
----------------------------------
GET /api/v1/progress/v3?subject=<subject>&days=30|90   (auth required)

Returns a rich progress payload for the Progress page v3:
  - narration         — static MVP string; Task 31 adds nightly LLM refresh
  - chart_series      — readiness % per day (from ReadinessSnapshot; MVP fills
                        missing days with current readiness)
  - readiness_current — latest readiness %
  - readiness_delta_14d — change vs 14 days ago
  - mastery_by_topic  — same shape as /topics/v3
  - session_history   — last 20 TutorSession rows
  - marker_history_compact — last 10 GradedUpload rows
  - weekly_stats      — this-week counts (Monday-week)
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import (
    GradedUpload,
    LearnerSubject,
    MasteryState,
    ProgressNarration,
    ReadinessSnapshot,
    Student,
    SyllabusTopic,
    TutorSession,
)
from app.services.narration import progress_narration as _pn_service
from app.services.readiness_service import compute_readiness_pct

router = APIRouter(prefix="/progress", tags=["progress"])


# ── Response schemas ──────────────────────────────────────────────────────────

class ChartPoint(BaseModel):
    date: str       # YYYY-MM-DD
    readiness: int  # 0..100 (rounded)


class MasteryTopic(BaseModel):
    id: str
    label: str
    mastery: int    # 0..100


class SessionRow(BaseModel):
    id: str
    date: str
    mode: str
    topic: Optional[str]
    duration_minutes: int
    delta_readiness: int


class MarkerRow(BaseModel):
    id: str
    date: str
    marks: Optional[int]
    max_marks: int
    delta_readiness: int


class WeeklyStats(BaseModel):
    sessions_this_week: int
    questions_attempted: int
    marks_scored: int
    marks_max: int
    time_in_app_minutes: int


class ProgressV3Response(BaseModel):
    narration: str
    chart_series: list[ChartPoint]
    readiness_current: int
    readiness_delta_14d: int
    mastery_by_topic: list[MasteryTopic]
    session_history: list[SessionRow]
    marker_history_compact: list[MarkerRow]
    weekly_stats: WeeklyStats


# ── Helpers ───────────────────────────────────────────────────────────────────

def _monday_of_week(d: date) -> date:
    """Return the Monday of the ISO week containing d."""
    return d - timedelta(days=d.weekday())


def _session_duration(session: TutorSession) -> int:
    """Return duration in whole minutes; 0 when ended_at is missing."""
    if session.ended_at is None or session.started_at is None:
        return 0
    delta = session.ended_at - session.started_at
    return max(0, int(delta.total_seconds() // 60))


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/v3", response_model=ProgressV3Response)
async def progress_v3(
    subject: str,
    days: int = Query(default=30, ge=1, le=90),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> ProgressV3Response:
    """Progress v3 — readiness chart + mastery + session & marker histories."""

    # ── Guard: subject must be registered ────────────────────────────────────
    ls_row = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.subject == subject,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if ls_row is None:
        raise HTTPException(status_code=404, detail="Subject not found for this student")

    syllabus_version: str = ls_row.syllabus_version or "2026.1"

    today = date.today()

    # ── Current readiness ────────────────────────────────────────────────────
    readiness_current_f = await compute_readiness_pct(
        db, student.id, subject, syllabus_version
    )
    readiness_current = int(round(readiness_current_f))

    # ── Chart series — ReadinessSnapshot for last `days` days ────────────────
    cutoff = today - timedelta(days=days - 1)
    snaps_rows = (await db.execute(
        select(ReadinessSnapshot.snapshot_date, ReadinessSnapshot.readiness_pct)
        .where(
            ReadinessSnapshot.student_id == student.id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date >= cutoff,
        )
        .order_by(ReadinessSnapshot.snapshot_date)
    )).all()

    snap_by_date: dict[date, int] = {
        r.snapshot_date: int(round(r.readiness_pct)) for r in snaps_rows
    }

    # Fill missing days with current readiness (MVP debt — no historical data)
    chart_series: list[ChartPoint] = []
    for i in range(days):
        d = cutoff + timedelta(days=i)
        readiness = snap_by_date.get(d, readiness_current)
        chart_series.append(ChartPoint(date=d.isoformat(), readiness=readiness))

    # ── 14-day delta ─────────────────────────────────────────────────────────
    d_14 = today - timedelta(days=14)
    snap_14 = (await db.execute(
        select(ReadinessSnapshot.readiness_pct).where(
            ReadinessSnapshot.student_id == student.id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date <= d_14,
        ).order_by(ReadinessSnapshot.snapshot_date.desc()).limit(1)
    )).scalar_one_or_none()

    readiness_delta_14d = (
        int(round(readiness_current_f - snap_14)) if snap_14 is not None else 0
    )

    # ── Mastery by topic ──────────────────────────────────────────────────────
    topic_rows = (await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name).where(
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == syllabus_version,
            SyllabusTopic.exam_board == (ls_row.exam_board or "edexcel"),
        ).order_by(SyllabusTopic.topic_name)
    )).all()

    mastery_map: dict[str, float] = {}
    if topic_rows:
        m_rows = (await db.execute(
            select(MasteryState.topic, MasteryState.mastery_score).where(
                MasteryState.student_id == student.id,
                MasteryState.subject == subject,
            )
        )).all()
        mastery_map = {r.topic: (r.mastery_score or 0.0) for r in m_rows}

    mastery_by_topic: list[MasteryTopic] = [
        MasteryTopic(
            id=t.topic_id,
            label=t.topic_name,
            mastery=int(round((mastery_map.get(t.topic_id, 0.0)) * 100)),
        )
        for t in topic_rows
    ]

    # ── Session history — last 20 ─────────────────────────────────────────────
    session_rows = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
        ).order_by(TutorSession.started_at.desc()).limit(20)
    )).scalars().all()

    session_history: list[SessionRow] = [
        SessionRow(
            id=str(s.id),
            date=s.started_at.date().isoformat() if s.started_at else today.isoformat(),
            mode=s.mode or "practice",
            topic=s.topic,
            duration_minutes=_session_duration(s),
            delta_readiness=0,  # MVP: no per-session delta stored; Task 31 enriches
        )
        for s in session_rows
    ]

    # ── Marker history compact — last 10 ─────────────────────────────────────
    marker_rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student.id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
        ).order_by(GradedUpload.created_at.desc()).limit(10)
    )).scalars().all()

    marker_history_compact: list[MarkerRow] = [
        MarkerRow(
            id=str(m.id),
            date=(
                m.created_at.date().isoformat()
                if m.created_at
                else today.isoformat()
            ),
            marks=m.marks_awarded,
            max_marks=m.max_marks,
            delta_readiness=0,  # MVP: not stored per-upload; Task 31 enriches
        )
        for m in marker_rows
    ]

    # ── Weekly stats — Monday-week ────────────────────────────────────────────
    week_start = datetime(
        *_monday_of_week(today).timetuple()[:3], tzinfo=timezone.utc
    )

    # Sessions this week
    sessions_this_week = (await db.execute(
        select(func.count(TutorSession.id)).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
            TutorSession.started_at >= week_start,
        )
    )).scalar() or 0

    # Marker submissions this week (graded only)
    marker_this_week = (await db.execute(
        select(
            func.count(GradedUpload.id),
            func.coalesce(func.sum(GradedUpload.marks_awarded), 0),
            func.coalesce(func.sum(GradedUpload.max_marks), 0),
        ).where(
            GradedUpload.student_id == student.id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
            GradedUpload.created_at >= week_start,
        )
    )).one()

    graded_count = marker_this_week[0] or 0
    marks_scored = int(marker_this_week[1] or 0)
    marks_max = int(marker_this_week[2] or 0)

    # Questions attempted ≈ graded_count (each upload is one question)
    questions_attempted = graded_count

    # Time in app — sum of session durations this week
    session_times = (await db.execute(
        select(TutorSession.started_at, TutorSession.ended_at).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
            TutorSession.started_at >= week_start,
            TutorSession.ended_at.isnot(None),
        )
    )).all()

    time_in_app_minutes = sum(
        max(0, int((r.ended_at - r.started_at).total_seconds() // 60))
        for r in session_times
    )

    weekly_stats = WeeklyStats(
        sessions_this_week=int(sessions_this_week),
        questions_attempted=questions_attempted,
        marks_scored=marks_scored,
        marks_max=marks_max,
        time_in_app_minutes=time_in_app_minutes,
    )

    # ── Narration — cached nightly narration (Task 31) ───────────────────────
    # 1. Check progress_narrations for today's cached row (written by cron at 03:00 UTC).
    # 2. If present, use it directly (effective 24h TTL via daily cron).
    # 3. If missing (first request of day before cron runs), generate on-demand as fallback.
    cached_row = (await db.execute(
        select(ProgressNarration.text).where(
            ProgressNarration.student_id == student.id,
            ProgressNarration.subject == subject,
            ProgressNarration.computed_date == today,
        ).limit(1)
    )).scalar_one_or_none()

    if cached_row is not None:
        narration = cached_row
    else:
        # On-demand fallback: build context from available data and call LLM
        cutoff_14 = today - timedelta(days=14)
        narration_snaps = (await db.execute(
            select(ReadinessSnapshot.snapshot_date, ReadinessSnapshot.readiness_pct)
            .where(
                ReadinessSnapshot.student_id == student.id,
                ReadinessSnapshot.subject == subject,
                ReadinessSnapshot.snapshot_date >= cutoff_14,
            )
            .order_by(ReadinessSnapshot.snapshot_date)
        )).all()

        readiness_series = [
            (r.snapshot_date, int(round(r.readiness_pct))) for r in narration_snaps
        ]

        # Derive top gainer / slipper from mastery_by_topic
        sorted_topics = sorted(mastery_by_topic, key=lambda t: t.mastery, reverse=True)
        top_gainer = sorted_topics[0].id if sorted_topics else None
        top_slipper = sorted_topics[-1].id if len(sorted_topics) > 1 else None

        try:
            pn_ctx = {
                "readiness_series": readiness_series,
                "top_gainer": top_gainer,
                "top_slipper": top_slipper,
            }
            narration = await _pn_service.generate(pn_ctx)
            narration = narration[:500]
        except Exception:
            # Final fallback: analytical static string (no praise, no speculation)
            if readiness_delta_14d > 0:
                narration = (
                    f"Readiness is at {readiness_current}%, "
                    f"up {readiness_delta_14d} points over the last 14 days."
                )
            elif readiness_delta_14d < 0:
                narration = (
                    f"Readiness is at {readiness_current}%, "
                    f"down {abs(readiness_delta_14d)} points over the last 14 days."
                )
            else:
                narration = f"Readiness is at {readiness_current}% — unchanged over the last 14 days."

    return ProgressV3Response(
        narration=narration,
        chart_series=chart_series,
        readiness_current=readiness_current,
        readiness_delta_14d=readiness_delta_14d,
        mastery_by_topic=mastery_by_topic,
        session_history=session_history,
        marker_history_compact=marker_history_compact,
        weekly_stats=weekly_stats,
    )
