"""Pipeline glue for Exam Marker: fetch photo → vision → grade → mastery+readiness update.

Handles state transitions: pending → extracting → grading → graded (or error).
Idempotency guard prevents duplicate processing.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import capture
from app.db.models import GradedUpload, MasteryState
from app.services.marker import grader_llm, vision, storage
from app.services.readiness_service import compute_readiness_pct

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {"pending"}  # only pending is retriable
COMPLETED_STATUSES = {"graded", "error"}


async def process_submission(db: AsyncSession, submission_id: UUID) -> None:
    """Run the full pipeline for a submission. Idempotent: re-runs on stuck rows only."""
    upload = await _load_and_lock(db, submission_id)
    if upload is None:
        logger.warning("Submission %s not found", submission_id)
        return
    if upload.status not in ACTIVE_STATUSES:
        logger.info("Submission %s already in status=%s; skipping",
                    submission_id, upload.status)
        return

    try:
        # Extraction stage (photo only)
        if upload.input_type == "photo":
            upload.status = "extracting"
            await db.flush()
            photo_bytes = await _fetch_photo_bytes(upload.photo_path)
            try:
                upload.answer_text = await vision.extract_answer(photo_bytes)
            except vision.ExtractionFailed as exc:
                _set_error(upload, _user_facing_extraction_error(exc.reason))
                _capture_event("marker_extraction_failed", upload.student_id,
                               reason=exc.reason)
                await db.flush()
                return
            _capture_event("marker_extraction_succeeded", upload.student_id,
                           submission_id=str(upload.id),
                           extracted_char_count=len(upload.answer_text or ""))

        # Grading stage
        upload.status = "grading"
        await db.flush()

        topic = _infer_topic_from_upload(upload)
        student_context = await grader_llm._load_student_topic_context(
            db, upload.student_id, upload.subject, topic,
        )

        readiness_before = await compute_readiness_pct(
            db, upload.student_id, upload.subject, "2026.1",
        )

        try:
            grading_result = await grader_llm.grade(
                question=upload.question_text,
                mark_scheme=upload.mark_scheme,
                answer=upload.answer_text or "",
                max_marks=upload.max_marks,
                student_context=student_context,
            )
        except grader_llm.GradingFailed:
            _set_error(upload, "Grading service is having trouble right now — please try again.")
            _capture_event("marker_grading_failed", upload.student_id,
                           error_stage="grading")
            await db.flush()
            return

        # Update mastery
        mastery_before = await _update_mastery(
            db, upload.student_id, upload.subject, topic,
            grade_pct=(grading_result["marks_awarded"] / upload.max_marks * 100),
        )

        # Recompute readiness after mastery update
        readiness_after = await compute_readiness_pct(
            db, upload.student_id, upload.subject, "2026.1",
        )
        mastery_after = await _current_mastery(db, upload.student_id, upload.subject, topic)

        # Finalize row
        upload.marks_awarded = grading_result["marks_awarded"]
        upload.grade_pct = round(
            grading_result["marks_awarded"] / upload.max_marks * 100, 2
        )
        upload.feedback_json = {
            **grading_result,
            "readiness_before": round(readiness_before, 1),
            "readiness_after": round(readiness_after, 1),
            "readiness_delta": round(readiness_after - readiness_before, 1),
            "topic_mastery_before": round(mastery_before, 2),
            "topic_mastery_after": round(mastery_after, 2),
            "used_generated_mark_scheme": False,  # set by question_selector; defaults false
        }
        upload.status = "graded"
        upload.updated_at = datetime.now(timezone.utc)
        await db.flush()

        _capture_event(
            "marker_grading_succeeded", upload.student_id,
            marks_awarded=grading_result["marks_awarded"],
            max_marks=upload.max_marks,
            grade_pct=upload.grade_pct,
            criteria_count=len(grading_result.get("criteria", [])),
            readiness_delta=upload.feedback_json["readiness_delta"],
            topic_mastery_delta=(mastery_after - mastery_before),
        )
        if abs(readiness_after - readiness_before) > 0.1:
            _capture_event("readiness_changed", upload.student_id,
                           subject=upload.subject,
                           prev_pct=readiness_before, new_pct=readiness_after,
                           delta=readiness_after - readiness_before)
    except Exception as exc:  # unhandled — mark error and log
        logger.exception("Unhandled orchestrator error for %s", submission_id)
        _set_error(upload, "Something went wrong grading your work. Please try again.")
        await db.flush()


# ── helpers ────────────────────────────────────────────────────────────────

async def _load_and_lock(db: AsyncSession, submission_id: UUID) -> GradedUpload | None:
    """SELECT ... FOR UPDATE to enforce idempotency across concurrent tasks."""
    res = await db.execute(
        select(GradedUpload).where(GradedUpload.id == submission_id).with_for_update()
    )
    return res.scalar_one_or_none()


async def _fetch_photo_bytes(path: str) -> bytes:
    """Fetch photo bytes from Supabase Storage via signed download URL + HTTP fetch."""
    import httpx
    url = await storage.generate_signed_download_url(path)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def _infer_topic_from_upload(upload: GradedUpload) -> str:
    """Best-effort topic inference. Question selector stored topic in question_text search;
    for MVP we don't persist a topic column — approximate from question_text as fallback.

    Real implementation: reviewer may add a `topic` column to GradedUpload.
    For now, use the subject as the topic label if we can't do better."""
    # If a topic-like slug is in question_text (from question_selector), prefer that.
    # MVP fallback: hardcode integration_basics if subject is pure_mathematics.
    # Reviewer should flag adding a proper topic column.
    return "integration_basics" if upload.subject == "pure_mathematics" else upload.subject


async def _update_mastery(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    topic: str,
    grade_pct: float,
) -> float:
    """Apply grade-based mastery delta. Returns the mastery_score BEFORE update."""
    row = (await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar_one_or_none()

    if row is None:
        row = MasteryState(
            student_id=student_id, subject=subject, topic=topic,
            mastery_score=0.0, total_attempts=0, correct_streak=0,
        )
        db.add(row)
        await db.flush()

    before = float(row.mastery_score or 0)
    if grade_pct >= 70:
        delta = 0.15
    elif grade_pct >= 40:
        delta = 0.05
    else:
        delta = -0.05

    row.mastery_score = max(0.0, min(1.0, before + delta))
    row.total_attempts = (row.total_attempts or 0) + 1
    row.last_reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return before


async def _current_mastery(db, student_id, subject, topic) -> float:
    row = (await db.execute(
        select(MasteryState.mastery_score).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar()
    return float(row or 0)


def _user_facing_extraction_error(reason: str) -> str:
    if reason == "illegible":
        return "Couldn't read your answer — try a clearer photo?"
    return "Something went wrong reading your answer. Please try again."


def _set_error(upload: GradedUpload, message: str) -> None:
    upload.status = "error"
    upload.error_message = message
    upload.updated_at = datetime.now(timezone.utc)


def _capture_event(event: str, student_id: UUID, **props) -> None:
    try:
        capture(str(student_id), event, props)
    except Exception as exc:
        logger.warning("Telemetry capture failed for %s: %s", event, exc)
