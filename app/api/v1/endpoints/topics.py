"""
app/api/v1/endpoints/topics.py
-------------------------------
GET /api/v1/topics/v3?subject=<subject>

Returns a list of all syllabus topics for the given subject with:
  - mastery percentage (0–100)
  - last_practised (relative string)
  - status band ("Mastered" / "Practising" / "Needs review" / "Not started")
  - prerequisite: always null (no prereq graph in SyllabusTopic — safe MVP fallback)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, SyllabusTopic, Student

router = APIRouter(prefix="/topics", tags=["topics"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _relative_date(dt: datetime | None) -> str:
    """Convert a UTC datetime to a human-readable relative string."""
    if dt is None:
        return "Never"
    now = datetime.now(timezone.utc)
    # Make dt timezone-aware if it isn't already
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    days = delta.days
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "last week"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks} weeks ago"
    months = days // 30
    if months < 2:
        return "last month"
    return f"{months} months ago"


def _mastery_status(mastery_score: float) -> str:
    """Convert a 0..1 mastery score to a display status string."""
    if mastery_score >= 0.7:
        return "Mastered"
    if mastery_score >= 0.4:
        return "Practising"
    if mastery_score > 0:
        return "Needs review"
    return "Not started"


# ── Response schema ──────────────────────────────────────────────────────────

class TopicV3(BaseModel):
    id: str
    label: str
    mastery: int                  # 0..100
    last_practised: str           # relative string or "Never"
    status: str                   # "Mastered" | "Practising" | "Needs review" | "Not started"
    prerequisite: None = None     # MVP: always null — no prereq graph in SyllabusTopic


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("/v3", response_model=list[TopicV3])
async def list_topics_v3(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> list[TopicV3]:
    """Syllabus browser v3 — all topics with mastery, recency, status.

    Prerequisites are always null in this MVP (SyllabusTopic has no prereq graph).
    """
    # Verify the student has this subject configured
    ls_row = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.subject == subject,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not ls_row:
        raise HTTPException(404, f"Subject '{subject}' not configured for this student")

    version = ls_row.syllabus_version

    # All syllabus topics in ordinal order
    syllabus_rows = (await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name, SyllabusTopic.ordinal)
        .where(
            SyllabusTopic.exam_board == ls_row.exam_board,
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
        )
        .order_by(SyllabusTopic.ordinal.asc())
    )).all()

    if not syllabus_rows:
        return []

    topic_ids = [r[0] for r in syllabus_rows]
    name_map = {r[0]: r[1] for r in syllabus_rows}

    # Mastery states for these topics (may be a subset)
    mastery_rows = (await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score, MasteryState.last_reviewed_at)
        .where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
            MasteryState.topic.in_(topic_ids),
        )
    )).all()

    mastery_map: dict[str, tuple[float, datetime | None]] = {
        r[0]: (r[1] or 0.0, r[2]) for r in mastery_rows
    }

    result: list[TopicV3] = []
    for topic_id in topic_ids:
        label = name_map[topic_id]
        score, last_reviewed = mastery_map.get(topic_id, (0.0, None))
        result.append(
            TopicV3(
                id=topic_id,
                label=label,
                mastery=round(score * 100),
                last_practised=_relative_date(last_reviewed),
                status=_mastery_status(score),
                prerequisite=None,
            )
        )

    return result
