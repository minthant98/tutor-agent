from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, SyllabusTopic, Student
from app.schemas.practice import PracticeTopic
from app.services.narration import practice_narration

router = APIRouter(prefix="/practice", tags=["practice"])


# ── v3 landing schema ────────────────────────────────────────────────────────

class WeakTopicItem(BaseModel):
    id: str
    label: str


class PracticeLandingResponse(BaseModel):
    narration: str
    weak_topics: list[WeakTopicItem]


@router.get("/topics", response_model=list[PracticeTopic])
async def list_practice_topics(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> list[PracticeTopic]:
    """Topics the student can practice on for the given subject.

    Ordering: attempted topics first (weakest mastery first),
    then unattempted syllabus topics in ordinal order. Limit 20.
    """
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

    # All syllabus topics for this board/subject/version, in ordinal order
    syllabus_rows = (await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name, SyllabusTopic.ordinal)
        .where(
            SyllabusTopic.exam_board == ls_row.exam_board,
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
        )
        .order_by(SyllabusTopic.ordinal.asc())
    )).all()

    name_map = {r[0]: r[1] for r in syllabus_rows}
    ordinal_map = {r[0]: r[2] for r in syllabus_rows}

    # Attempted topics for this student
    attempted_rows = (await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
        .order_by(MasteryState.mastery_score.asc())
    )).all()

    attempted_topics = {r[0] for r in attempted_rows}
    attempted = [
        PracticeTopic(
            topic_id=t,
            topic_name=name_map.get(t, t),
            mastery_pct=int((m or 0) * 100),
            has_attempts=True,
        )
        for t, m in attempted_rows
        if t in name_map
    ]

    unattempted = [
        PracticeTopic(
            topic_id=t,
            topic_name=name_map[t],
            mastery_pct=0,
            has_attempts=False,
        )
        for t in name_map
        if t not in attempted_topics
    ]

    return (attempted + unattempted)[:20]


@router.get("/v3/landing", response_model=PracticeLandingResponse)
async def practice_v3_landing(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> PracticeLandingResponse:
    """Practice v3 landing data: Alex narration + top 2 weak topics for this subject."""

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

    # Get top 2 weak topics (lowest mastery among attempted topics)
    weak_rows = (await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
        .order_by(MasteryState.mastery_score.asc())
        .limit(2)
    )).all()

    # Resolve topic names from syllabus
    version = ls_row.syllabus_version
    topic_ids = [r[0] for r in weak_rows]
    name_rows = (await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name)
        .where(
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
            SyllabusTopic.topic_id.in_(topic_ids),
        )
    )).all() if topic_ids else []
    name_map = {r[0]: r[1] for r in name_rows}

    weak_topics = [
        WeakTopicItem(
            id=topic_id,
            label=name_map.get(topic_id, topic_id.replace("_", " ").title()),
        )
        for topic_id, _ in weak_rows
    ]

    # Generate narration — skip LLM call when there is no practice data yet
    if not weak_topics:
        narration = "No practice data yet. Complete a session to build your profile."
    else:
        narration_context = {
            "subject": subject,
            "weak_topics": [
                {
                    "topic_id": topic_id,
                    "topic_name": name_map.get(topic_id, topic_id.replace("_", " ").title()),
                    "mastery_pct": int((mastery or 0) * 100),
                }
                for topic_id, mastery in weak_rows
            ],
        }
        narration = await practice_narration.generate(narration_context)

    return PracticeLandingResponse(narration=narration, weak_topics=weak_topics)
