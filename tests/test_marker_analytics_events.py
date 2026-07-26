"""Tests for Marker v3 analytics events (Task 29).

Covers:
1. marker_time_to_grade_seconds fires when a submission is graded
2. marker_time_to_submit_seconds fires when time_to_submit_seconds is supplied
3. marker_recommended_practice_completed fires when a bridged TutorSession ends
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.models import GradedUpload, TutorSession
from app.services.marker import orchestrator, grader_llm


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_upload(student_id, input_type="typed", answer_text="x^2", max_marks=4,
                 time_to_submit_seconds=None):
    return GradedUpload(
        student_id=student_id,
        subject="pure_mathematics",
        exam_board="edexcel",
        question_id="q_analytics_test",
        question_text="Q",
        mark_scheme="MS",
        max_marks=max_marks,
        input_type=input_type,
        answer_text=answer_text if input_type == "typed" else None,
        photo_path=None if input_type == "typed" else "student/test.jpg",
        status="pending",
        time_to_submit_seconds=time_to_submit_seconds,
    )


VALID_GRADING = {
    "marks_awarded": 3,
    "criteria": [],
    "summary": "Good",
    "improvement": "Be more precise.",
}


# ── Backend: orchestrator analytics ──────────────────────────────────────────

class TestMarkerOrchestratorAnalytics:
    @pytest.mark.asyncio
    async def test_time_to_grade_seconds_fired_on_success(
        self, db_session, student_with_subject, syllabus_edexcel_seeded
    ):
        """marker_time_to_grade_seconds must be captured when grading succeeds."""
        upload = _make_upload(student_with_subject.id)
        db_session.add(upload)
        await db_session.flush()

        captured_events: list[tuple[str, str, dict]] = []

        def spy_capture(distinct_id, event, props):
            captured_events.append((distinct_id, event, props))

        with patch("app.services.marker.orchestrator._capture_event",
                   side_effect=lambda e, sid, **kw: spy_capture(str(sid), e, kw)), \
             patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
            await orchestrator.process_submission(db_session, upload.id)

        event_names = [e[1] for e in captured_events]
        assert "marker_time_to_grade_seconds" in event_names, (
            f"Expected marker_time_to_grade_seconds in {event_names}"
        )

        grade_event = next(e for e in captured_events if e[1] == "marker_time_to_grade_seconds")
        props = grade_event[2]
        assert "seconds" in props
        assert isinstance(props["seconds"], float)
        assert props["seconds"] >= 0
        assert props["submission_id"] == str(upload.id)

    @pytest.mark.asyncio
    async def test_time_to_submit_seconds_fired_when_supplied(
        self, db_session, student_with_subject, syllabus_edexcel_seeded
    ):
        """marker_time_to_submit_seconds fires only when time_to_submit_seconds is non-null."""
        upload = _make_upload(student_with_subject.id, time_to_submit_seconds=47.3)
        db_session.add(upload)
        await db_session.flush()

        captured_events: list[tuple[str, str, dict]] = []

        def spy_capture(distinct_id, event, props):
            captured_events.append((distinct_id, event, props))

        with patch("app.services.marker.orchestrator._capture_event",
                   side_effect=lambda e, sid, **kw: spy_capture(str(sid), e, kw)), \
             patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
            await orchestrator.process_submission(db_session, upload.id)

        event_names = [e[1] for e in captured_events]
        assert "marker_time_to_submit_seconds" in event_names, (
            f"Expected marker_time_to_submit_seconds in {event_names}"
        )

        submit_event = next(e for e in captured_events if e[1] == "marker_time_to_submit_seconds")
        assert submit_event[2]["seconds"] == pytest.approx(47.3)

    @pytest.mark.asyncio
    async def test_time_to_submit_seconds_not_fired_when_null(
        self, db_session, student_with_subject, syllabus_edexcel_seeded
    ):
        """marker_time_to_submit_seconds must NOT fire when time_to_submit_seconds is None."""
        upload = _make_upload(student_with_subject.id, time_to_submit_seconds=None)
        db_session.add(upload)
        await db_session.flush()

        captured_events: list[tuple[str, str, dict]] = []

        def spy_capture(distinct_id, event, props):
            captured_events.append((distinct_id, event, props))

        with patch("app.services.marker.orchestrator._capture_event",
                   side_effect=lambda e, sid, **kw: spy_capture(str(sid), e, kw)), \
             patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
            await orchestrator.process_submission(db_session, upload.id)

        event_names = [e[1] for e in captured_events]
        assert "marker_time_to_submit_seconds" not in event_names


# ── Backend: session end loop-close event ────────────────────────────────────

class TestRecommendedPracticeCompleted:
    @pytest.mark.asyncio
    async def test_recommended_practice_completed_fires_when_bridged_session_ends(
        self, authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
    ):
        """When a TutorSession with source_submission_id is ended via POST /sessions/end,
        marker_recommended_practice_completed must be captured with the source_submission_id.
        """
        source_id = uuid.uuid4()

        # Create a bridged session directly in DB
        session = TutorSession(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            session_type="drill_in",
            segment_plan=[],
            messages=[{"role": "tutor", "content": "Hello"}],
            source_submission_id=source_id,
        )
        db_session.add(session)
        await db_session.flush()

        captured: list[tuple[str, str, dict]] = []

        def spy(distinct_id, event, props=None):
            captured.append((distinct_id, event, props or {}))

        with patch("app.api.v1.endpoints.sessions.capture", side_effect=spy):
            resp = await authed_client.post(f"/api/v1/sessions/end?session_id={session.id}")

        assert resp.status_code == 200, resp.text

        completed_events = [e for e in captured if e[1] == "marker_recommended_practice_completed"]
        assert len(completed_events) == 1, (
            f"Expected exactly 1 marker_recommended_practice_completed, got {len(completed_events)}. "
            f"All events: {[e[1] for e in captured]}"
        )

        props = completed_events[0][2]
        assert props["source_submission_id"] == str(source_id)
        assert props["session_id"] == str(session.id)

    @pytest.mark.asyncio
    async def test_recommended_practice_completed_not_fired_for_non_bridged_session(
        self, authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
    ):
        """Sessions without source_submission_id must NOT fire the loop-close event."""
        session = TutorSession(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            session_type="drill_in",
            segment_plan=[],
            messages=[{"role": "tutor", "content": "Hello"}],
            source_submission_id=None,
        )
        db_session.add(session)
        await db_session.flush()

        captured: list[tuple[str, str, dict]] = []

        def spy(distinct_id, event, props=None):
            captured.append((distinct_id, event, props or {}))

        with patch("app.api.v1.endpoints.sessions.capture", side_effect=spy):
            resp = await authed_client.post(f"/api/v1/sessions/end?session_id={session.id}")

        assert resp.status_code == 200, resp.text

        completed_events = [e for e in captured if e[1] == "marker_recommended_practice_completed"]
        assert len(completed_events) == 0, (
            f"Expected no marker_recommended_practice_completed for non-bridged session, "
            f"got: {completed_events}"
        )
