"""Regression tests: resume_session must preserve preferences, session_type,
session_version, segment_plan, and current_segment_idx from the DB.

Finding 2 from Phase C code review.
Tests target the pure _rebuild_resume_state helper to avoid HTTP context.
"""
import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.session_service import _rebuild_resume_state


def _make_student(preferences=None):
    """Create a mock Student object."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.exam_board = "edexcel"
    s.exam_level = "a_level"
    s.subscription_tier = "free"
    s.exam_date = None
    s.preferences = preferences or {}
    return s


def _make_db_session(
    subject="pure_mathematics",
    session_type="practice",
    session_version=2,
    segment_plan=None,
    current_segment_idx=0,
    topic=None,
    student_id=None,
):
    """Create a mock TutorSession DB object."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.student_id = student_id or uuid.uuid4()
    s.subject = subject
    s.topic = topic
    s.session_type = session_type
    s.session_version = session_version
    s.segment_plan = segment_plan if segment_plan is not None else []
    s.current_segment_idx = current_segment_idx
    s.messages = []
    return s


def test_rebuild_preserves_preferences_session_type_segment_fields():
    """Core regression: all four fields must survive the state rebuild."""
    student = _make_student(preferences={"worked_examples": True})
    seg_plan = [
        {"idx": 0, "intent": "reinforce", "handler": "practice", "topic": "differentiation",
         "why": "weak area", "target_minutes": 10, "status": "in_progress", "config": {}}
    ]
    db_session = _make_db_session(
        student_id=student.id,
        session_type="practice",
        session_version=2,
        segment_plan=seg_plan,
        current_segment_idx=1,
    )
    messages = [
        {"role": "tutor", "content": "Hello!"},
        {"role": "student", "content": "Hi!"},
    ]

    state = _rebuild_resume_state(
        session_id=str(db_session.id),
        student=student,
        db_session=db_session,
        messages=messages,
        weak_topics=["differentiation"],
    )

    assert state["preferences"] == {"worked_examples": True}, (
        "preferences must be restored from student.preferences"
    )
    assert state["session_type"] == "practice", (
        "session_type must be restored from db_session.session_type"
    )
    assert state["segment_plan"] == seg_plan, (
        "segment_plan must be restored from db_session.segment_plan"
    )
    assert state["current_segment_idx"] == 1, (
        "current_segment_idx must be restored from db_session.current_segment_idx"
    )


def test_rebuild_defaults_empty_preferences_when_student_has_none():
    """If student.preferences is None, state preferences should be empty dict (not None)."""
    student = _make_student(preferences=None)
    db_session = _make_db_session(student_id=student.id)

    state = _rebuild_resume_state(
        session_id=str(db_session.id),
        student=student,
        db_session=db_session,
        messages=[],
        weak_topics=[],
    )

    assert state["preferences"] == {}


def test_rebuild_defaults_empty_segment_plan_when_db_has_none():
    """If db_session.segment_plan is None, state segment_plan should be []."""
    student = _make_student()
    db_session = _make_db_session(student_id=student.id, segment_plan=None)

    state = _rebuild_resume_state(
        session_id=str(db_session.id),
        student=student,
        db_session=db_session,
        messages=[],
        weak_topics=[],
    )

    assert state["segment_plan"] == []


def test_rebuild_phase_computed_from_turn_count():
    """Phase is determined from the number of student messages in the history."""
    student = _make_student()
    db_session = _make_db_session(student_id=student.id)

    # 0 student messages -> intro
    state = _rebuild_resume_state(
        str(db_session.id), student, db_session, [], []
    )
    assert state["session_phase"] == "intro"
    assert state["turn_count"] == 0

    # 1 student message -> diagnostic
    messages_1 = [{"role": "student", "content": "q1"}]
    state1 = _rebuild_resume_state(
        str(db_session.id), student, db_session, messages_1, []
    )
    assert state1["session_phase"] == "diagnostic"

    # 4 student messages -> main
    messages_4 = [{"role": "student", "content": f"q{i}"} for i in range(4)]
    state4 = _rebuild_resume_state(
        str(db_session.id), student, db_session, messages_4, []
    )
    assert state4["session_phase"] == "main"
    assert state4["turn_count"] == 4
