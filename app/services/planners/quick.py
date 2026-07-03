"""1-segment plan on a user-chosen topic. 3 questions, ~5 min."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    _format_topic,
    _validate_topic,
)


class QuickPlanner:
    session_type = "quick_practice"
    requires_topic = True

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        assert topic is not None  # dispatcher already checks requires_topic
        await _validate_topic(db, student_id, subject, topic)

        segment = {
            "idx": 0,
            "intent": "reinforce",
            "handler": "practice",
            "topic": topic,
            "why": f"Quick practice on {_format_topic(topic)}.",
            "target_minutes": 5,
            "status": "in_progress",
            "config": {
                "mode": "quick_practice",
                "max_questions": 3,
                "allow_hints": True,
            },
        }
        reason: PlannerReason = {
            "topic_selections": [
                {
                    "topic": topic,
                    "mastery": None,
                    "chosen_intent": "reinforce",
                    "last_practiced_days": None,
                    "signal": "user_selected",
                }
            ]
        }
        return {"plan": [segment], "reason": reason}
