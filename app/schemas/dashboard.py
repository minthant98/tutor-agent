"""
app/schemas/dashboard.py
------------------------
Pydantic v2 schemas for the GET /api/v1/dashboard/{subject} response.
"""
from datetime import date, datetime
from pydantic import BaseModel


class SegmentOut(BaseModel):
    idx: int
    intent: str
    handler: str
    topic: str | None
    why: str
    target_minutes: int
    status: str


class TodayFocusOut(BaseModel):
    shape: str
    segment_plan: list[SegmentOut]
    total_minutes: int
    generated_at: datetime


class ResumeSessionOut(BaseModel):
    session_id: str
    completed_segments: int
    total_segments: int


class TopicMastery(BaseModel):
    topic: str
    topic_name: str
    mastery_pct: int


class TrendOut(BaseModel):
    prev_pct: float
    new_pct: float
    delta: float


class RecentActivityOut(BaseModel):
    last_studied: date | None
    summary: str | None   # e.g. "Integration Practice · scored 78%"
    cold: bool            # true if >3 days since last study


class DashboardPayload(BaseModel):
    subject: str
    exam_date: date | None
    days_until_exam: int | None
    target_grade: str
    predicted_grade: str | None
    readiness_pct: float
    readiness_trend: TrendOut | None
    today_focus: TodayFocusOut
    resume_session: ResumeSessionOut | None
    recent_activity: RecentActivityOut | None
    strong_topics: list[TopicMastery]
    weak_topics: list[TopicMastery]
    subject_options: list[str]  # for subject switcher
