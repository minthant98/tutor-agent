import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select
from app.db.models import GradedUpload, MasteryState
from app.services.marker import orchestrator, vision, grader_llm


def _make_upload(student_id, subject="pure_mathematics", input_type="typed",
                 answer_text="x^2 + C", max_marks=6):
    return GradedUpload(
        student_id=student_id, subject=subject, exam_board="edexcel",
        question_id="q1", question_text="Q", mark_scheme="MS",
        max_marks=max_marks, input_type=input_type,
        answer_text=answer_text if input_type == "typed" else None,
        photo_path=None if input_type == "typed" else "student/sub.jpg",
        status="pending",
    )


VALID_GRADING = {
    "marks_awarded": 4,
    "criteria": [], "summary": "s", "improvement": "i",
}


@pytest.mark.asyncio
async def test_orchestrator_typed_flow_transitions_to_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    db_session.add(upload)
    await db_session.flush()

    with patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "graded"
    assert upload.marks_awarded == 4
    assert upload.grade_pct == pytest.approx(66.67, abs=0.5)
    assert upload.feedback_json["marks_awarded"] == 4
    assert upload.feedback_json["readiness_after"] >= upload.feedback_json["readiness_before"]


@pytest.mark.asyncio
async def test_orchestrator_photo_flow_calls_vision(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="photo",
                          answer_text=None)
    db_session.add(upload)
    await db_session.flush()

    with patch.object(orchestrator, "_fetch_photo_bytes",
                     new=AsyncMock(return_value=b"fake_bytes")), \
         patch.object(vision, "extract_answer",
                     new=AsyncMock(return_value="x^2 + C")), \
         patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "graded"
    assert upload.answer_text == "x^2 + C"


@pytest.mark.asyncio
async def test_orchestrator_extraction_illegible_sets_error(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="photo",
                          answer_text=None)
    db_session.add(upload)
    await db_session.flush()

    with patch.object(orchestrator, "_fetch_photo_bytes",
                     new=AsyncMock(return_value=b"fake_bytes")), \
         patch.object(vision, "extract_answer",
                     new=AsyncMock(side_effect=vision.ExtractionFailed(reason="illegible"))):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "error"
    assert "clearer" in upload.error_message.lower() or "read" in upload.error_message.lower()


@pytest.mark.asyncio
async def test_orchestrator_grading_failure_sets_error(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    db_session.add(upload)
    await db_session.flush()

    with patch.object(grader_llm, "grade",
                     new=AsyncMock(side_effect=grader_llm.GradingFailed(reason="invalid_json_after_retry"))):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "error"


@pytest.mark.asyncio
async def test_orchestrator_idempotent_skip_already_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    upload.status = "graded"
    upload.marks_awarded = 5
    upload.feedback_json = {"marks_awarded": 5}
    db_session.add(upload)
    await db_session.flush()

    graded_call_count = {"n": 0}
    async def counter(*args, **kwargs):
        graded_call_count["n"] += 1
        return VALID_GRADING

    with patch.object(grader_llm, "grade", side_effect=counter):
        await orchestrator.process_submission(db_session, upload.id)

    # grade should NOT be called
    assert graded_call_count["n"] == 0


@pytest.mark.asyncio
async def test_orchestrator_feedback_json_reflects_used_generated_mark_scheme(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Regression: feedback_json.used_generated_mark_scheme must read from the upload
    row, not be hardcoded to False."""
    upload = _make_upload(student_with_subject.id, input_type="typed")
    upload.used_generated_mark_scheme = True
    db_session.add(upload)
    await db_session.flush()

    with patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "graded"
    assert upload.feedback_json["used_generated_mark_scheme"] is True


@pytest.mark.asyncio
async def test_orchestrator_updates_mastery_on_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    # Seed prior mastery so we can measure delta
    db_session.add(MasteryState(
        student_id=student_with_subject.id, subject="pure_mathematics",
        topic="integration_basics", mastery_score=0.30, total_attempts=2,
    ))
    upload = _make_upload(student_with_subject.id, input_type="typed", max_marks=6)
    upload.question_text = "Integrate x^2"
    # Attach topic to upload's mark_scheme so orchestrator can look it up
    db_session.add(upload)
    await db_session.flush()

    high_score = {**VALID_GRADING, "marks_awarded": 5}  # 83% → +0.15
    with patch.object(grader_llm, "grade", new=AsyncMock(return_value=high_score)), \
         patch.object(orchestrator, "_infer_topic_from_upload",
                     return_value="integration_basics"):
        await orchestrator.process_submission(db_session, upload.id)

    ms = (await db_session.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_with_subject.id,
            MasteryState.topic == "integration_basics",
        )
    )).scalar_one()
    assert ms.mastery_score == pytest.approx(0.45, abs=0.01)
    assert ms.total_attempts == 3
