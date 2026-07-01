"""Response schemas for admin endpoints."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class StudentProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    onboarded_at: Optional[datetime]
    subscription_tier: str
    preferences: dict

    model_config = {"from_attributes": True}


class SubjectResponse(BaseModel):
    id: str
    subject: str
    exam_board: str
    exam_date: Optional[date]
    target_grade: str
    syllabus_version: str
    is_draft: bool

    model_config = {"from_attributes": True}


class MasteryResponse(BaseModel):
    topic: str
    mastery_score: float
    total_attempts: int
    is_weak: bool

    model_config = {"from_attributes": True}


class TodayFocusResponse(BaseModel):
    focus_date: date
    shape: str
    segment_plan: list
    reasoning: list

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    session_type: str
    session_version: int
    segment_plan: list
    current_segment_idx: int
    started_at: datetime

    model_config = {"from_attributes": True}


class RecentSessionResponse(BaseModel):
    id: str
    subject: str
    topic: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    session_type: str

    model_config = {"from_attributes": True}


class InspectStudentResponse(BaseModel):
    profile: StudentProfileResponse
    subjects: list[SubjectResponse]
    mastery: list[MasteryResponse]
    latest_today_focus: Optional[TodayFocusResponse]
    active_session: Optional[SessionResponse]
    recent_sessions: list[RecentSessionResponse]

    model_config = {"from_attributes": True}
