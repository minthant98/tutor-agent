from pydantic import BaseModel, Field
from typing import Literal
import uuid
from datetime import datetime


class StartSessionRequest(BaseModel):
    subject: str = Field(description="mathematics, physics, chemistry, biology")
    exam_date: str | None = Field(None, description="ISO date: 2026-06-15")
    topic: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    message: str
    is_new_student: bool = False


class MessageRequest(BaseModel):
    session_id: str
    message: str = Field(max_length=4000)
    signal: Literal["explain", "guide"] | None = None


class MessageResponse(BaseModel):
    session_id: str
    response: str
    session_phase: str
    weak_topics: list[str]
    turn_count: int


class EndSessionResponse(BaseModel):
    session_id: str
    turns: int
    weak_topics: list[str]
    summary: str


class TopicMastery(BaseModel):
    topic: str
    mastery_score: float
    total_attempts: int
    is_weak: bool

    model_config = {"from_attributes": True}


class ProgressResponse(BaseModel):
    subject: str
    overall_mastery: float
    weak_topics: list[TopicMastery]
    strong_topics: list[TopicMastery]
    total_sessions: int
