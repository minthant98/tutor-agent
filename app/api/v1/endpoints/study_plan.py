import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import MasteryState, Student, StudyPlan
from app.schemas.schemas import StudyPlanResponse, StudyPlanWeek
from app.services.study_plan_service import generate_plan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/study-plan", tags=["study-plan"])


async def _get_weak_topics(db: AsyncSession, student_id, subject: str) -> list[str]:
    result = await db.execute(
        select(MasteryState.topic).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.is_weak == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


async def _build_response(record: StudyPlan) -> StudyPlanResponse:
    return StudyPlanResponse(
        subject=record.subject,
        weeks_remaining=record.weeks_remaining,
        plan=[StudyPlanWeek(**w) for w in record.plan],
        generated_at=record.generated_at,
    )


# ── GET /study-plan ───────────────────────────────────────────────────────────

@router.get("", response_model=StudyPlanResponse)
async def get_study_plan(
    subject: str = "mathematics",
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudyPlan).where(
            StudyPlan.student_id == student.id,
            StudyPlan.subject == subject,
        )
    )
    record = result.scalar_one_or_none()

    if record:
        return await _build_response(record)

    return await _generate_and_save(student, subject, db)


# ── POST /study-plan/regenerate ───────────────────────────────────────────────

@router.post(
    "/regenerate",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_study_plan(
    subject: str = "mathematics",
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudyPlan).where(
            StudyPlan.student_id == student.id,
            StudyPlan.subject == subject,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.flush()

    return await _generate_and_save(student, subject, db)


async def _generate_and_save(
    student: Student,
    subject: str,
    db: AsyncSession,
) -> StudyPlanResponse:
    from app.services.study_plan_service import _weeks_until
    weak_topics = await _get_weak_topics(db, student.id, subject)
    weeks = _weeks_until(student.exam_date)

    plan_data = await generate_plan(
        subject=subject,
        exam_board=student.exam_board,
        exam_date=student.exam_date,
        weak_topics=weak_topics,
    )

    record = StudyPlan(
        student_id=student.id,
        subject=subject,
        weeks_remaining=weeks,
        plan=plan_data,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return await _build_response(record)
