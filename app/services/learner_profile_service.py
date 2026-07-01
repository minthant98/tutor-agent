# app/services/learner_profile_service.py
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearnerSubject, Student
from app.core.syllabus_seed import SYLLABUS_VERSION

SUPPORTED_COMBOS: set[tuple[str, str, str]] = {
    ("pure_mathematics", "edexcel", "a_level"),
    ("pure_mathematics", "cambridge", "a_level"),
}


def is_supported_combo(subject: str, board: str, level: str = "a_level") -> bool:
    return (subject, board, level) in SUPPORTED_COMBOS


async def get_or_create_draft(db: AsyncSession, student_id: UUID) -> list[LearnerSubject]:
    res = await db.execute(select(LearnerSubject).where(LearnerSubject.student_id == student_id))
    return list(res.scalars().all())


async def upsert_subject_draft(db: AsyncSession, student_id: UUID, subject: str, **fields) -> LearnerSubject:
    res = await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = LearnerSubject(
            student_id=student_id,
            subject=subject,
            exam_board=fields.get("exam_board", "edexcel"),
            exam_level=fields.get("exam_level", "a_level"),
            target_grade=fields.get("target_grade", "A"),
            syllabus_version=SYLLABUS_VERSION,
            is_draft=True,
        )
        db.add(row)
    for k, v in fields.items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.flush()
    return row


async def list_subjects(db: AsyncSession, student_id: UUID, include_drafts: bool = False) -> list[LearnerSubject]:
    stmt = select(LearnerSubject).where(LearnerSubject.student_id == student_id)
    if not include_drafts:
        stmt = stmt.where(LearnerSubject.is_draft == False)  # noqa: E712
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def finalize_drafts(db: AsyncSession, student_id: UUID) -> int:
    rows = await get_or_create_draft(db, student_id)
    count = 0
    for r in rows:
        if r.is_draft:
            r.is_draft = False
            count += 1
    if count > 0:
        student = await db.get(Student, student_id)
        if student:
            student.onboarded_at = datetime.now(timezone.utc)
            student.onboarding_complete = True
    await db.flush()
    return count


async def update_subject(db: AsyncSession, student_id: UUID, subject_id: UUID, **fields) -> LearnerSubject:
    row = await db.get(LearnerSubject, subject_id)
    if row is None or row.student_id != student_id:
        raise ValueError("Subject not found")
    for k, v in fields.items():
        if hasattr(row, k) and k not in ("id", "student_id", "is_draft"):
            setattr(row, k, v)
    await db.flush()
    return row


async def update_preferences(db: AsyncSession, student_id: UUID, prefs: dict) -> Student:
    student = await db.get(Student, student_id)
    if student is None:
        raise ValueError("Student not found")
    allowed = {"worked_examples", "visual", "step_by_step", "practice"}
    student.preferences = {k: bool(v) for k, v in prefs.items() if k in allowed}
    await db.flush()
    return student
