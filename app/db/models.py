import uuid
from datetime import datetime, date

from sqlalchemy import (
    JSON, Boolean, Date, DateTime, Float,
    ForeignKey, Integer, String, func,
)
from sqlalchemy.dialects.postgresql import UUID
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
    messages: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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