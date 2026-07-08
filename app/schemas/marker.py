"""Pydantic schemas for the Exam Marker endpoints."""
from datetime import datetime
from typing import Literal
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


class SubmissionCreateOut(BaseModel):
    submission_id: str
    upload_url: str | None = None
    upload_path: str | None = None


class UploadedNotifyOut(BaseModel):
    ok: bool


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
