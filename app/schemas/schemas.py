from pydantic import BaseModel, Field
from typing import Literal, Any
import uuid
from datetime import datetime


class StartSessionRequest(BaseModel):
    subject: str = Field(description="mathematics, physics, chemistry, biology")
    mode: Literal["explain", "quiz", "review", "exam_practice"] = "explain"
    topic: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    message: str


class MessageRequest(BaseModel):
    session_id: str
    message: str = Field(max_length=4000)


class MessageResponse(BaseModel):
    session_id: str
    response: str
    intent: str | None
    topic: str | None
    sources_used: int
    rules_action: str | None
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