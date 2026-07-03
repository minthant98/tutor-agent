"""Pydantic model for validating PlannerReason payloads before analytics/persistence."""
from pydantic import BaseModel


class TopicSelectionModel(BaseModel):
    topic: str
    mastery: float | None = None
    chosen_intent: str | None = None
    last_practiced_days: int | None = None
    signal: str


class PlannerReasonModel(BaseModel):
    topic_selections: list[TopicSelectionModel]
