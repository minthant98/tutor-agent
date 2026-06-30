# app/api/v1/endpoints/account.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student, LearnerSubject
from app.services import learner_profile_service as lps, readiness_service
from app.schemas.account import (
    AccountOut, ProfileOut, SubjectOut, PreferencesOut, BillingOut,
    SubjectPatch, ProfilePatch,
)

router = APIRouter(prefix="/account", tags=["account"])


async def _subject_out(db: AsyncSession, ls: LearnerSubject) -> SubjectOut:
    pct = await readiness_service.compute_readiness_pct(
        db, ls.student_id, ls.subject, ls.syllabus_version
    )
    return SubjectOut(
        id=str(ls.id),
        subject=ls.subject,
        exam_board=ls.exam_board,
        exam_level=ls.exam_level,
        exam_date=ls.exam_date,
        target_grade=ls.target_grade,
        current_grade=ls.current_grade,
        readiness_pct=pct,
    )


async def _build_account_out(db: AsyncSession, student: Student) -> AccountOut:
    subjects = await lps.list_subjects(db, student.id)
    return AccountOut(
        profile=ProfileOut(name=student.name, email=student.email),
        subjects=[await _subject_out(db, s) for s in subjects],
        preferences=PreferencesOut(**{
            k: bool(v)
            for k, v in (student.preferences or {}).items()
            if k in {"worked_examples", "visual", "step_by_step", "practice"}
        }),
        billing=BillingOut(
            tier=student.subscription_tier,
            status=student.subscription_status,
        ),
    )


@router.get("", response_model=AccountOut)
async def get_account(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    return await _build_account_out(db, student)


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def patch_subject(
    subject_id: str,
    body: SubjectPatch,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> SubjectOut:
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if "exam_board" in updates:
        ls = await db.get(LearnerSubject, UUID(subject_id))
        if ls is None or ls.student_id != student.id:
            raise HTTPException(404, "Subject not found")
        if not lps.is_supported_combo(ls.subject, updates["exam_board"], "a_level"):
            raise HTTPException(400, "Unsupported board")
    ls = await lps.update_subject(db, student.id, UUID(subject_id), **updates)
    return await _subject_out(db, ls)


@router.patch("/preferences", response_model=AccountOut)
async def patch_preferences(
    body: dict,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    await lps.update_preferences(db, student.id, body)
    student = await db.get(Student, student.id)
    return await _build_account_out(db, student)


@router.patch("/profile", response_model=ProfileOut)
async def patch_profile(
    body: ProfilePatch,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    if body.name:
        student.name = body.name.strip()
        await db.flush()
    return ProfileOut(name=student.name, email=student.email)


@router.delete("/email")
async def delete_email():
    raise HTTPException(501, "Contact support")


@router.delete("")
async def delete_account():
    raise HTTPException(501, "Contact support")
