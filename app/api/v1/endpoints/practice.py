from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, SyllabusTopic, Student
from app.schemas.practice import PracticeTopic

router = APIRouter(prefix="/practice", tags=["practice"])


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
