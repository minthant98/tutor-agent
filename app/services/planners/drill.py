"""3-segment plan on ONE topic — teach → reinforce → assess.

Loosely models cognitive progression: worked example → guided → independent.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    _format_topic,
    _validate_topic,
)


class DrillInPlanner:
    session_type = "drill_in"
    requires_topic = True

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        assert topic is not None
        await _validate_topic(db, student_id, subject, topic)
        name = _format_topic(topic)

        segments = [
            {
                "idx": 0,
                "intent": "teach",
                "handler": "practice",
                "topic": topic,
                "why": f"Building up {name}.",
                "target_minutes": 4,
                "status": "in_progress",
                "config": {
                    "mode": "drill_in",
                    "system_prompt_addendum": "Open with a worked example before asking.",
                    "allow_hints": True,
                    "max_questions": 2,
                },
            },
            {
                "idx": 1,
                "intent": "reinforce",
                "handler": "practice",
                "topic": topic,
                "why": "Now try something harder.",
                "target_minutes": 4,
                "status": "pending",
                "config": {
                    "mode": "drill_in",
                    "allow_hints": True,
                    "max_questions": 2,
                },
            },
            {
                "idx": 2,
                "intent": "assess",
                "handler": "practice",
                "topic": topic,
                "why": "No hints this round — test what you've learned.",
                "target_minutes": 2,
                "status": "pending",
                "config": {
                    "mode": "drill_in",
                    "allow_hints": False,
                    "max_questions": 2,
                },
            },
        ]
        reason: PlannerReason = {
            "topic_selections": [
                {
                    "topic": topic,
                    "mastery": None,
                    "chosen_intent": "teach",
                    "last_practiced_days": None,
                    "signal": "drill_in_from_dashboard",
                }
            ]
        }
        return {"plan": segments, "reason": reason}
