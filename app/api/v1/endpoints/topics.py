"""
app/api/v1/endpoints/topics.py
-------------------------------
GET /api/v1/topics/v3?subject=<subject>
  Returns a list of all syllabus topics for the given subject with:
  - mastery percentage (0–100)
  - last_practised (relative string)
  - status band ("Mastered" / "Practising" / "Needs review" / "Not started")
  - prerequisite: always null (no prereq graph in SyllabusTopic — safe MVP fallback)

GET /api/v1/topics/v3/{topic_id}?subject=<subject>
  Returns detailed 5-section payload for a single topic:
  topic, common_mistakes, recent_attempts, recommended_practice_href, related_topics
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import GradedUpload, LearnerSubject, MasteryState, SyllabusTopic, Student
from app.services.narration import topic_mistakes

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


# ── Topic detail v3 response schema ──────────────────────────────────────────

class TopicDetailInfo(BaseModel):
    id: str
    label: str
    mastery: int                   # 0..100
    syllabus_ref: str              # e.g. "Edexcel 9MA0 · Topic 4.3" — derived from SyllabusTopic
    target_grade: str


class CommonMistake(BaseModel):
    text: str
    evidence_submission_ids: list[str]


class RecentAttempt(BaseModel):
    id: str
    created_at: str                 # ISO 8601
    marks: int
    max_marks: int
    question_preview: str


class RelatedTopic(BaseModel):
    id: str
    label: str
    relation: str                   # e.g. "prerequisite"


class TopicDetailV3(BaseModel):
    topic: TopicDetailInfo
    common_mistakes: list[CommonMistake]
    recent_attempts: list[RecentAttempt]
    recommended_practice_href: str
    related_topics: list[RelatedTopic]


# ── Helper: derive syllabus ref ───────────────────────────────────────────────

def _syllabus_ref(exam_board: str, subject: str, ordinal: int) -> str:
    """Derive a human-readable syllabus reference string.

    Example: "Edexcel · Topic 4.3"
    SyllabusTopic does not store a spec code so we use exam_board + ordinal.
    """
    board_label = exam_board.capitalize()
    topic_label = f"Topic {ordinal}"
    return f"{board_label} · {topic_label}"


# ── Topic detail endpoint ─────────────────────────────────────────────────────

@router.get("/v3/{topic_id}", response_model=TopicDetailV3)
async def get_topic_v3_detail(
    topic_id: str,
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> TopicDetailV3:
    """Topic detail v3 — five-section payload.

    Sections (in fixed order):
      1. topic — overview info (mastery, syllabus_ref, target_grade)
      2. common_mistakes — Alex-generated, evidence-backed, empty for fresh students
      3. recent_attempts — last 5 GradedUpload rows for student+subject
      4. recommended_practice_href — deep link to practice mode
      5. related_topics — empty list (no prereq graph in SyllabusTopic)
    """
    # Verify student has this subject configured
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

    # Look up SyllabusTopic for label + ordinal
    syllabus_row = (await db.execute(
        select(SyllabusTopic).where(
            SyllabusTopic.exam_board == ls_row.exam_board,
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
            SyllabusTopic.topic_id == topic_id,
        )
    )).scalar_one_or_none()
    if not syllabus_row:
        raise HTTPException(404, f"Topic '{topic_id}' not found in syllabus")

    # Mastery state
    mastery_row = (await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
            MasteryState.topic == topic_id,
        )
    )).scalar_one_or_none()
    mastery_score = float(mastery_row.mastery_score) if mastery_row else 0.0
    mastery_pct = round(mastery_score * 100)

    # Syllabus ref — derived from exam_board + ordinal (no spec code stored)
    syllabus_ref = _syllabus_ref(ls_row.exam_board, subject, syllabus_row.ordinal)

    # Target grade from LearnerSubject
    target_grade = ls_row.target_grade or "A"

    # Common mistakes — Alex-generated, evidence-backed
    # Returns [] for fresh students (no attempts)
    raw_mistakes = await topic_mistakes.generate(
        db=db,
        student_id=student.id,
        topic_id=topic_id,
        subject=subject,
    )
    common_mistakes = [
        CommonMistake(
            text=m["text"],
            evidence_submission_ids=m["evidence_submission_ids"],
        )
        for m in raw_mistakes
    ]

    # Recent attempts — last 5 GradedUpload rows for student + subject (graded only)
    # GradedUpload has no topic column; filter by subject. MVP best-effort.
    upload_rows = (await db.execute(
        select(GradedUpload)
        .where(
            GradedUpload.student_id == student.id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
        )
        .order_by(GradedUpload.created_at.desc())
        .limit(5)
    )).scalars().all()

    recent_attempts = [
        RecentAttempt(
            id=str(row.id),
            created_at=row.created_at.isoformat(),
            marks=row.marks_awarded or 0,
            max_marks=row.max_marks,
            question_preview=(row.question_text or "")[:80],
        )
        for row in upload_rows
    ]

    # Recommended practice link — deep link to drill_in mode for this topic
    recommended_practice_href = (
        f"/practice/plan?mode=drill_in&topic={topic_id}&subject={subject}"
    )

    # Related topics — SyllabusTopic has no prereq relations → empty list (MVP)
    related_topics: list[RelatedTopic] = []

    return TopicDetailV3(
        topic=TopicDetailInfo(
            id=topic_id,
            label=syllabus_row.topic_name,
            mastery=mastery_pct,
            syllabus_ref=syllabus_ref,
            target_grade=target_grade,
        ),
        common_mistakes=common_mistakes,
        recent_attempts=recent_attempts,
        recommended_practice_href=recommended_practice_href,
        related_topics=related_topics,
    )
