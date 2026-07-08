from app.db.models import (
    Student, TutorSession, LearnerSubject, SyllabusTopic,
    ReadinessSnapshot, Notification, TodayFocusHistory,
)


def test_graded_upload_model_imports():
    from app.db.models import GradedUpload
    assert hasattr(GradedUpload, "__tablename__")
    assert GradedUpload.__tablename__ == "graded_uploads"


def test_graded_upload_has_expected_columns():
    from app.db.models import GradedUpload
    cols = GradedUpload.__table__.columns
    expected = {
        "id", "student_id", "subject", "exam_board",
        "question_id", "question_text", "mark_scheme", "max_marks",
        "input_type", "photo_path", "answer_text",
        "marks_awarded", "grade_pct", "feedback_json",
        "status", "error_message", "created_at", "updated_at",
        "used_generated_mark_scheme",
    }
    assert expected.issubset(set(cols.keys()))


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
