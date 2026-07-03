"""Practice mode planner registry.

To add a new mode: create a planner file (implementing the Planner protocol
from base.py) and register it in PLANNERS. The /sessions/start dispatcher
looks up planners by session_type — it does not need to change.
"""
from app.services.planners.base import (
    BuildResult,
    Planner,
    PlannerReason,
    TopicSelection,
)

PLANNERS: dict[str, Planner] = {}

__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "PLANNERS",
]
