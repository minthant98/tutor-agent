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
from app.services.planners.quick import QuickPlanner
from app.services.planners.weak import WeakAreasPlanner
from app.services.planners.drill import DrillInPlanner

PLANNERS: dict[str, Planner] = {
    QuickPlanner.session_type: QuickPlanner(),
    WeakAreasPlanner.session_type: WeakAreasPlanner(),
    DrillInPlanner.session_type: DrillInPlanner(),
}

__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "PLANNERS",
]
