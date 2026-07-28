"""Pydantic schemas for the Exam Marker endpoints."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class QuestionCandidateOut(BaseModel):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int
    paper_ref: str
    topic: str
    used_generated_mark_scheme: bool


class SubmissionCreateIn(BaseModel):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int = Field(ge=1, le=50)
    input_type: Literal["photo", "typed"]
    answer_text: str | None = None
    photo_extension: Literal["jpg", "jpeg", "png", "webp"] | None = None
    used_generated_mark_scheme: bool = False
    # Client-measured seconds from question shown to submit — used for marker_time_to_submit_seconds
    time_to_submit_seconds: float | None = None


class SubmissionCreateOut(BaseModel):
    submission_id: str
    upload_url: str | None = None
    upload_path: str | None = None


class UploadedNotifyOut(BaseModel):
    ok: bool


class MemoryRef(BaseModel):
    text: str
    evidence_days_ago: int


class RecommendedPractice(BaseModel):
    topic_id: str
    sub_skill: str
    blurb: str


class SubmissionOut(BaseModel):
    id: str
    status: str
    subject: str
    exam_board: str
    question_id: str
    question_text: str
    max_marks: int
    input_type: str
    answer_text: str | None = None
    marks_awarded: int | None = None
    grade_pct: float | None = None
    feedback_json: dict | None = None
    photo_url: str | None = None  # fresh signed URL if photo path exists
    error_message: str | None = None
    created_at: datetime
    # Task 25: top-level readiness fields (1-decimal precision, from feedback_json)
    readiness_before: Optional[float] = None
    readiness_after: Optional[float] = None
    # Task 25: Alex memory reference — most recent same-topic attempt or null
    memory_ref: Optional[MemoryRef] = None
    # Task 27: recommended next step — derived from missed criteria
    recommended_practice: Optional[RecommendedPractice] = None
