from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, SyllabusTopic, Student, TutorSession
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


# ── GET /practice/plan ────────────────────────────────────────────────────────

class PlanSegment(BaseModel):
    intent: str
    topic: str


class PlanResponse(BaseModel):
    narration: str
    segments: list[PlanSegment]
    minutes: int


_SEGMENT_MINUTES = {
    "quick_practice": 5,
    "weak_areas": 6,
    "drill_in": 4,
}


@router.get("/plan", response_model=PlanResponse)
async def get_practice_plan(
    mode: str,
    topic: str | None = None,
    skill: str | None = None,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    """Return a planner-generated segment plan for the transparency screen.

    - `mode`: one of quick_practice, weak_areas, drill_in
    - `topic`: required for drill_in and quick_practice
    - `skill`: Marker bridge — when present, narration references Exam Marker result
    """
    from app.services.planners import PLANNERS

    if mode not in PLANNERS:
        raise HTTPException(400, f"Unknown mode '{mode}'")

    planner = PLANNERS[mode]
    if planner.requires_topic and not topic:
        raise HTTPException(400, f"topic required for mode '{mode}'")

    # Look up subject from the student's most recent active LearnerSubject
    ls_row = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        ).order_by(LearnerSubject.id.asc()).limit(1)
    )).scalar_one_or_none()

    if not ls_row:
        raise HTTPException(404, "No subject configured for this student")

    subject = ls_row.subject
    result = await planner.build(db, student.id, subject, topic)
    raw_segments = result["plan"]

    # Resolve topic display names from SyllabusTopic
    topic_ids = list({s["topic"] for s in raw_segments if s.get("topic")})
    name_rows = []
    if topic_ids:
        name_result = await db.execute(
            select(SyllabusTopic.topic_id, SyllabusTopic.topic_name).where(
                SyllabusTopic.subject == subject,
                SyllabusTopic.version == ls_row.syllabus_version,
                SyllabusTopic.topic_id.in_(topic_ids),
            )
        )
        name_rows = list(name_result.all())
    name_map = {r[0]: r[1] for r in name_rows}

    segments = [
        PlanSegment(
            intent=s["intent"],
            topic=name_map.get(s["topic"] or "", s.get("topic") or "").replace("_", " ").title()
            if s.get("topic") not in name_map
            else name_map[s["topic"]],
        )
        for s in raw_segments
        if s.get("topic")  # skip consolidate/mistakes segments with no topic
    ]

    # Estimate minutes
    seg_min = _SEGMENT_MINUTES.get(mode, 5)
    minutes = seg_min * len(segments)

    # Narration
    if skill:
        skill_label = skill.replace("_", " ").title()
        narration = f"Coming from your Exam Marker result — targeting {skill_label}."
    else:
        narration_context = {
            "mode": mode,
            "subject": subject,
            "segments": [{"intent": s.intent, "topic": s.topic} for s in segments],
        }
        narration = await practice_narration.generate(narration_context)

    return PlanResponse(narration=narration, segments=segments, minutes=minutes)


# ── GET /practice/drill-in/resume ─────────────────────────────────────────────

class DrillResumeProgress(BaseModel):
    current: int
    total: int


class DrillResumeResponse(BaseModel):
    session_id: str
    topic_label: str
    progress: DrillResumeProgress


@router.get("/drill-in/resume", response_model=DrillResumeResponse | None)
async def get_drill_in_resume(
    topic: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> DrillResumeResponse | None:
    """Return an active drill_in session for the given topic, or null if none.

    Reuses the active_session logic: find the most recent unended drill_in session
    whose segment_plan has the given topic.
    """
    result = await db.execute(
        select(TutorSession)
        .where(
            TutorSession.student_id == student.id,
            TutorSession.session_type == "drill_in",
            TutorSession.ended_at.is_(None),
        )
        .order_by(TutorSession.started_at.desc())
        .limit(10)
    )
    sessions = result.scalars().all()

    # Filter to sessions whose segment_plan includes the requested topic
    for session in sessions:
        plan = session.segment_plan or []
        if not any(s.get("topic") == topic for s in plan):
            continue

        # Compute progress: how many segments completed
        current_idx = session.current_segment_idx or 0
        total = len(plan)

        # Resolve topic label
        ls_row = (await db.execute(
            select(LearnerSubject).where(
                LearnerSubject.student_id == student.id,
                LearnerSubject.is_draft == False,  # noqa: E712
            ).limit(1)
        )).scalar_one_or_none()

        topic_label = topic.replace("_", " ").title()
        if ls_row:
            name_result = await db.execute(
                select(SyllabusTopic.topic_name).where(
                    SyllabusTopic.topic_id == topic,
                    SyllabusTopic.subject == ls_row.subject,
                    SyllabusTopic.version == ls_row.syllabus_version,
                ).limit(1)
            )
            row = name_result.scalar_one_or_none()
            if row:
                topic_label = row

        return DrillResumeResponse(
            session_id=str(session.id),
            topic_label=topic_label,
            progress=DrillResumeProgress(current=current_idx, total=total),
        )

    return None
