from app.db.models import (
    Student, TutorSession, LearnerSubject, SyllabusTopic,
    ReadinessSnapshot, Notification, TodayFocusHistory,
)


def test_new_models_importable():
    for cls in (LearnerSubject, SyllabusTopic, ReadinessSnapshot,
                Notification, TodayFocusHistory):
        assert hasattr(cls, "__tablename__")


def test_student_has_new_columns():
    assert "preferences" in Student.__table__.columns
    assert "onboarded_at" in Student.__table__.columns
    assert "is_admin" in Student.__table__.columns


def test_session_has_segment_columns():
    cols = TutorSession.__table__.columns
    for name in ("session_type", "session_version", "segment_plan", "current_segment_idx"):
        assert name in cols
