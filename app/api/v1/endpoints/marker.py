"""Exam Marker HTTP endpoints."""
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.marker_limit import check_marker_limit
from app.core.telemetry import capture
from app.db.database import get_db
from app.db.models import GradedUpload, LearnerSubject, Student
from app.schemas.marker import (
    MemoryRef,
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

# ── Upload URL endpoint ────────────────────────────────────────────────────────

_CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class UploadUrlRequest(BaseModel):
    content_type: str   # e.g. "image/jpeg"
    filename: str       # original filename for logging


class UploadUrlResponse(BaseModel):
    signed_url: str
    photo_path: str


@router.post("/submissions/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    body: UploadUrlRequest,
    student: Student = Depends(get_current_student),
) -> UploadUrlResponse:
    """Return a short-lived signed PUT URL so the client can upload directly to Supabase Storage."""
    ext = _CONTENT_TYPE_EXT.get(body.content_type.lower())
    if ext is None:
        raise HTTPException(415, f"Unsupported content_type '{body.content_type}'. Allowed: {sorted(_CONTENT_TYPE_EXT)}")

    photo_path = f"uploads/{student.id}/{uuid4()}.{ext}"
    signed_url = await generate_signed_upload_url(photo_path, body.content_type)
    return UploadUrlResponse(signed_url=signed_url, photo_path=photo_path)


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

    # Task 25: extract readiness fields from feedback_json (1-decimal precision)
    readiness_before: Optional[float] = None
    readiness_after: Optional[float] = None
    if upload.feedback_json and isinstance(upload.feedback_json, dict):
        rb = upload.feedback_json.get("readiness_before")
        ra = upload.feedback_json.get("readiness_after")
        if rb is not None:
            readiness_before = round(float(rb), 1)
        if ra is not None:
            readiness_after = round(float(ra), 1)

    # Task 25: build memory_ref from most-recent prior same-topic grade
    memory_ref: Optional[MemoryRef] = None
    if upload.status == "graded":
        try:
            from app.services.marker.orchestrator import _infer_topic_from_upload
            topic = _infer_topic_from_upload(upload)
            student_context = await _load_student_topic_context_excluding_current(
                db, student.id, upload.subject, topic, exclude_id=upload.id
            )
            if student_context["recent_grades"]:
                prev = student_context["recent_grades"][0]  # most recent
                current_pct = float(upload.grade_pct or 0)
                prev_pct = prev["grade_pct"]
                trend_word = "higher" if current_pct > prev_pct else "lower" if current_pct < prev_pct else "similar"
                topic_label = topic.replace("_", " ").title()
                memory_ref = MemoryRef(
                    text=(
                        f"Your previous {topic_label} attempt scored {prev_pct:.0f}% "
                        f"— this one is {trend_word}."
                    ),
                    evidence_days_ago=prev["days_ago"],
                )
        except Exception:
            pass  # memory_ref stays None — non-fatal

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
        readiness_before=readiness_before,
        readiness_after=readiness_after,
        memory_ref=memory_ref,
    )


async def _load_student_topic_context_excluding_current(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    topic: str,
    exclude_id: UUID,
) -> dict:
    """Load student topic context but exclude the current submission from recent_grades.

    This prevents the current submission from appearing as its own memory reference.
    """
    from app.services.marker import grader_llm
    from app.db.models import GradedUpload
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    grade_rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student_id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
            GradedUpload.id != exclude_id,
        ).order_by(GradedUpload.created_at.desc()).limit(3)
    )).scalars().all()

    recent_grades = []
    for row in grade_rows:
        improvement = ""
        if row.feedback_json and isinstance(row.feedback_json, dict):
            improvement = row.feedback_json.get("improvement", "")
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_ago = (now - created).days
        recent_grades.append({
            "grade_pct": float(row.grade_pct or 0),
            "marks_awarded": row.marks_awarded or 0,
            "max_marks": row.max_marks,
            "improvement": improvement,
            "days_ago": days_ago,
        })

    return {
        "recent_grades": recent_grades,
        "mastery_trend": {},
        "recent_practice_mistakes": [],
    }


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


# ── Marker v3 landing ─────────────────────────────────────────────────────────

FREE_TIER_REFRESH_LIMIT = 5


class V3QuestionOut(BaseModel):
    id: str
    text: str
    max_marks: int
    paper_ref: str


class V3RecentSubmissionOut(BaseModel):
    id: str
    created_at: datetime
    marks: Optional[int]
    max_marks: int
    delta_readiness: Optional[int]
    question_preview: str


class MarkerV3LandingOut(BaseModel):
    narration: str
    question: V3QuestionOut
    refresh_count_used: int
    refresh_limit: Optional[int]
    tier: str
    recent_submissions: list[V3RecentSubmissionOut]


@router.get("/v3/landing", response_model=MarkerV3LandingOut)
async def get_v3_landing(
    subject: str = Query("pure_mathematics"),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> MarkerV3LandingOut:
    """Marker v3 landing — narration + suggested question + refresh state + recent submissions."""
    from app.services.narration import marker_narration

    # Resolve learner subject (use query param subject; fall back to first configured)
    ls = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.subject == subject,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalars().first()

    if ls is None:
        # Fall back to any non-draft subject
        ls = (await db.execute(
            select(LearnerSubject).where(
                LearnerSubject.student_id == student.id,
                LearnerSubject.is_draft == False,  # noqa: E712
            ).order_by(LearnerSubject.created_at.asc())
        )).scalars().first()

    if ls is None:
        raise HTTPException(404, "No subject configured for this student")

    # Resolve tier (Student.subscription_tier — defaults to free)
    tier = getattr(student, "subscription_tier", "free") or "free"
    is_pro = tier == "pro"

    # Count today's graded_uploads (= refresh_count_used)
    today_start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    refresh_count_used = (await db.execute(
        select(func.count()).select_from(GradedUpload).where(
            GradedUpload.student_id == student.id,
            GradedUpload.created_at >= today_start,
        )
    )).scalar_one()

    refresh_limit: Optional[int] = None if is_pro else FREE_TIER_REFRESH_LIMIT

    # Pick suggested question (reuse existing pick_question logic)
    candidate = await pick_question(db, student.id, ls.subject, ls.exam_board)

    # Recent submissions (last 5)
    recent_rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student.id,
        ).order_by(GradedUpload.created_at.desc()).limit(5)
    )).scalars().all()

    recent_submissions: list[V3RecentSubmissionOut] = []
    for r in recent_rows:
        delta: Optional[int] = None
        if r.feedback_json and isinstance(r.feedback_json, dict):
            delta = r.feedback_json.get("readiness_delta")
        recent_submissions.append(V3RecentSubmissionOut(
            id=str(r.id),
            created_at=r.created_at,
            marks=r.marks_awarded,
            max_marks=r.max_marks,
            delta_readiness=delta,
            question_preview=r.question_text[:80],
        ))

    # Build narration context
    recent_grades = [
        float(r.grade_pct) for r in recent_rows if r.grade_pct is not None
    ]
    avg_grade_pct = round(sum(recent_grades) / len(recent_grades), 1) if recent_grades else None

    narration_context = {
        "recent_grade_pct": avg_grade_pct,
        "weak_topic": candidate.get("topic"),
        "today_submission_count": int(refresh_count_used),
    }
    narration = await marker_narration.generate(narration_context)

    return MarkerV3LandingOut(
        narration=narration,
        question=V3QuestionOut(
            id=candidate["question_id"],
            text=candidate["question_text"],
            max_marks=candidate["max_marks"],
            paper_ref=candidate["paper_ref"],
        ),
        refresh_count_used=int(refresh_count_used),
        refresh_limit=refresh_limit,
        tier=tier,
        recent_submissions=recent_submissions,
    )
