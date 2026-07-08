"""Exam Marker HTTP endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.marker_limit import check_marker_limit
from app.core.telemetry import capture
from app.db.database import get_db
from app.db.models import GradedUpload, LearnerSubject, Student
from app.schemas.marker import (
    QuestionCandidateOut,
    SubmissionCreateIn,
    SubmissionCreateOut,
    SubmissionOut,
    UploadedNotifyOut,
)
from app.services.marker.orchestrator import process_submission
from app.services.marker.question_selector import pick_question
from app.services.marker.storage import (
    build_photo_path,
    generate_signed_download_url,
    generate_signed_upload_url,
)

router = APIRouter(prefix="/marker", tags=["marker"])


@router.get("/next-question", response_model=QuestionCandidateOut)
async def get_next_question(
    # TODO(#3-follow-up): re-enable topic query param after adding topic column to GradedUpload
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> QuestionCandidateOut:
    ls = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        ).order_by(LearnerSubject.created_at.asc())
    )).scalars().first()
    if ls is None:
        raise HTTPException(404, "No subject configured for this student")

    candidate = await pick_question(
        db, student.id, ls.subject, ls.exam_board,
    )
    try:
        capture(str(student.id), "marker_question_served", {
            "subject": ls.subject, "board": ls.exam_board,
            "topic": candidate["topic"],
            "question_id": candidate["question_id"],
            "paper_ref": candidate["paper_ref"],
            "used_generated_mark_scheme": candidate["used_generated_mark_scheme"],
        })
    except Exception:
        pass
    return QuestionCandidateOut(**candidate)


@router.post("/submissions", response_model=SubmissionCreateOut, status_code=201)
async def post_submission(
    body: SubmissionCreateIn,
    student: Student = Depends(check_marker_limit),
    db: AsyncSession = Depends(get_db),
) -> SubmissionCreateOut:
    if body.input_type == "photo":
        if not body.photo_extension:
            raise HTTPException(400, "photo_extension required for photo submissions")
    if body.input_type == "typed":
        if not body.answer_text or not body.answer_text.strip():
            raise HTTPException(400, "answer_text required for typed submissions")

    ls = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        ).order_by(LearnerSubject.created_at.asc())
    )).scalars().first()
    if ls is None:
        raise HTTPException(404, "No subject configured for this student")

    upload = GradedUpload(
        id=uuid4(),
        student_id=student.id,
        subject=ls.subject,
        exam_board=ls.exam_board,
        question_id=body.question_id,
        question_text=body.question_text,
        mark_scheme=body.mark_scheme,
        max_marks=body.max_marks,
        input_type=body.input_type,
        answer_text=body.answer_text if body.input_type == "typed" else None,
        used_generated_mark_scheme=body.used_generated_mark_scheme,
        status="pending",
    )

    upload_url = None
    upload_path = None
    if body.input_type == "photo":
        upload_path = build_photo_path(student.id, upload.id, body.photo_extension)
        upload.photo_path = upload_path
        upload_url = await generate_signed_upload_url(upload_path, "image/jpeg")

    db.add(upload)
    await db.commit()

    try:
        capture(str(student.id), "marker_submission_created", {
            "input_type": body.input_type,
            "subscription_tier": student.subscription_tier,
            "used_generated_mark_scheme": body.used_generated_mark_scheme,
        })
    except Exception:
        pass

    return SubmissionCreateOut(
        submission_id=str(upload.id),
        upload_url=upload_url,
        upload_path=upload_path,
    )


@router.post("/submissions/{submission_id}/uploaded", response_model=UploadedNotifyOut)
async def notify_uploaded(
    submission_id: UUID,
    background: BackgroundTasks,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> UploadedNotifyOut:
    upload = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.id == submission_id,
            GradedUpload.student_id == student.id,
        )
    )).scalar_one_or_none()
    if upload is None:
        raise HTTPException(404, "Submission not found")
    background.add_task(_process_in_background, submission_id)
    return UploadedNotifyOut(ok=True)


async def _process_in_background(submission_id: UUID) -> None:
    """BackgroundTask wrapper — opens its own DB session."""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await process_submission(db, submission_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: UUID,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> SubmissionOut:
    upload = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.id == submission_id,
            GradedUpload.student_id == student.id,
        )
    )).scalar_one_or_none()
    if upload is None:
        raise HTTPException(404, "Submission not found")

    photo_url = None
    if upload.photo_path and upload.status == "graded":
        try:
            photo_url = await generate_signed_download_url(upload.photo_path)
        except Exception:
            photo_url = None

    return SubmissionOut(
        id=str(upload.id),
        status=upload.status,
        subject=upload.subject,
        exam_board=upload.exam_board,
        question_id=upload.question_id,
        question_text=upload.question_text,
        max_marks=upload.max_marks,
        input_type=upload.input_type,
        answer_text=upload.answer_text,
        marks_awarded=upload.marks_awarded,
        grade_pct=float(upload.grade_pct) if upload.grade_pct is not None else None,
        feedback_json=upload.feedback_json,
        photo_url=photo_url,
        error_message=upload.error_message,
        created_at=upload.created_at,
    )


@router.get("/submissions", response_model=list[SubmissionOut])
async def list_submissions(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> list[SubmissionOut]:
    rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student.id,
        ).order_by(GradedUpload.created_at.desc()).limit(limit).offset(offset)
    )).scalars().all()
    return [
        SubmissionOut(
            id=str(r.id), status=r.status,
            subject=r.subject, exam_board=r.exam_board,
            question_id=r.question_id, question_text=r.question_text,
            max_marks=r.max_marks, input_type=r.input_type,
            answer_text=r.answer_text, marks_awarded=r.marks_awarded,
            grade_pct=float(r.grade_pct) if r.grade_pct is not None else None,
            feedback_json=r.feedback_json,
            photo_url=None,  # history list doesn't include signed URLs (fetched per row)
            error_message=r.error_message,
            created_at=r.created_at,
        )
        for r in rows
    ]
