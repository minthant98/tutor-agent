import uuid
from datetime import datetime, date

import sqlalchemy as sa
from sqlalchemy import (
    JSON, Boolean, Date, DateTime, Float,
    ForeignKey, Index, Integer, String, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Academic profile
    exam_board: Mapped[str] = mapped_column(String(50), default="edexcel")
    exam_level: Mapped[str] = mapped_column(String(20), default="a_level")
    subjects: Mapped[list] = mapped_column(JSON, default=list)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Subscription
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_status: Mapped[str] = mapped_column(String(20), default="active")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    sessions: Mapped[list["TutorSession"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    mastery_records: Mapped[list["MasteryState"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    study_plan: Mapped["StudyPlan | None"] = relationship(
        back_populates="student", cascade="all, delete-orphan", uselist=False
    )


class TutorSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(String(50), default="explain")
    session_type: Mapped[str] = mapped_column(String(20), default="practice", nullable=False)
    session_version: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    segment_plan: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    current_segment_idx: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    state: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Marker bridge: set when this session was started from a Marker submission result.
    # Enables loop-close analytics: marker_recommended_practice_completed.
    source_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )

    student: Mapped["Student"] = relationship(back_populates="sessions")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    weeks_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[list] = mapped_column(JSON, nullable=False)  # list of week dicts
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="study_plan")


class MasteryState(Base):
    __tablename__ = "mastery_state"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)

    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_streak: Mapped[int] = mapped_column(Integer, default=0)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False)

    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    student: Mapped["Student"] = relationship(back_populates="mastery_records")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LearnerSubject(Base):
    __tablename__ = "learner_subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_level: Mapped[str] = mapped_column(String(20), nullable=False, default="a_level")
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_grade: Mapped[str] = mapped_column(String(2), nullable=False)
    current_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    syllabus_version: Mapped[str] = mapped_column(String(20), nullable=False, default="2026.1")
    recommended_minutes_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject", name="uq_learner_subjects_student_subject"),)


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_topic_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("exam_board", "subject", "version", "topic_id",
                                       name="uq_syllabus_board_subject_version_topic"),)


class ReadinessSnapshot(Base):
    __tablename__ = "readiness_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    readiness_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject", "snapshot_date",
                                       name="uq_readiness_student_subject_date"),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TodayFocusHistory(Base):
    __tablename__ = "today_focus_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    focus_date: Mapped[date] = mapped_column(Date, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(20), nullable=False)
    shape: Mapped[str] = mapped_column(String(50), nullable=False)
    segment_plan: Mapped[list] = mapped_column(JSON, nullable=False)
    reasoning: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "subject", "focus_date",
                                       name="uq_today_focus_student_subject_date"),)


class GradedUpload(Base):
    __tablename__ = "graded_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)

    question_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Qdrant point id
    question_text: Mapped[str] = mapped_column(String, nullable=False)     # cached from Qdrant
    mark_scheme: Mapped[str] = mapped_column(String, nullable=False)       # cached from Qdrant
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False)

    input_type: Mapped[str] = mapped_column(String(20), nullable=False)    # "photo" | "typed"
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(String, nullable=True)

    marks_awarded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    used_generated_mark_scheme: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=sa.text("false")
    )

    # Client-measured seconds from question shown to submit (for analytics)
    time_to_submit_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Observation(Base):
    """Alex observations with traceability — up to 3 per student/subject/week."""

    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    trace_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    week_of: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_observations_student_subject_week", "student_id", "subject", "week_of"),
    )
