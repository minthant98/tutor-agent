"""3-segment plan across 2 weakest topics + mistakes review.

Adaptive intent selection: each segment's intent is derived from the topic's
current mastery via _intent_from_mastery. A near-zero-mastery topic gets a
worked example (teach), a partial-mastery topic gets repetition (reinforce),
and a solid topic gets a no-hint pressure test (assess).
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    TopicSelection,
    _days_since_last_practice,
    _first_syllabus_topics,
    _format_topic,
    _intent_from_mastery,
    _weakest_topics_with_attempts,
)


class WeakAreasPlanner:
    session_type = "weak_areas"
    requires_topic = False

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=2)
        fallback_flags = [False] * len(weak)

        if len(weak) < 2:
            exclude = {t for t, _ in weak}
            fallback = await _first_syllabus_topics(
                db, student_id, subject, exclude=exclude, limit=2 - len(weak)
            )
            for t in fallback:
                weak.append((t, 0.0))
                fallback_flags.append(True)

        selections: list[TopicSelection] = []
        segments: list[dict] = []

        for i, (topic_id, mastery) in enumerate(weak):
            intent = _intent_from_mastery(mastery)
            days = await _days_since_last_practice(db, student_id, subject, topic_id)
            config: dict = {"mode": "weak_areas", "allow_hints": True, "max_questions": 3}
            if intent == "teach":
                config["system_prompt_addendum"] = "Open with a worked example before asking."
            elif intent == "assess":
                config["allow_hints"] = False
                config["max_questions"] = 2

            segments.append({
                "idx": i,
                "intent": intent,
                "handler": "practice",
                "topic": topic_id,
                "why": _why_for(intent, topic_id, mastery),
                "target_minutes": 6,
                "status": "in_progress" if i == 0 else "pending",
                "config": config,
            })
            selections.append({
                "topic": topic_id,
                "mastery": mastery,
                "chosen_intent": intent,
                "last_practiced_days": days,
                "signal": _signal_for(i, mastery, fallback_flags[i]),
            })

        # Trailing mistakes-review segment
        segments.append({
            "idx": 2,
            "intent": "consolidate",
            "handler": "mistakes",
            "topic": None,
            "why": "Review recent mistakes across your session history.",
            "target_minutes": 3,
            "status": "pending",
            "config": {"mode": "weak_areas", "source_sessions_days": 7},
        })
        selections.append({
            "topic": "__mistakes__",
            "mastery": None,
            "chosen_intent": "consolidate",
            "last_practiced_days": None,
            "signal": "mistakes_from_recent_sessions",
        })

        return {"plan": segments, "reason": {"topic_selections": selections}}


def _why_for(intent: str, topic: str, mastery: float) -> str:
    name = _format_topic(topic)
    if intent == "teach":
        return f"{name} is nearly unlearned ({int(mastery * 100)}%). Let's build it up."
    if intent == "reinforce":
        return f"{name} is at {int(mastery * 100)}%. Reinforcement time."
    return f"{name} looks solid ({int(mastery * 100)}%). Let's pressure-test it."


def _signal_for(idx: int, mastery: float, is_fallback: bool) -> str:
    if is_fallback:
        return "syllabus_seed_fallback"
    if idx == 0:
        return "weakest_topic_low_mastery" if mastery < 0.20 else "weakest_topic_partial_mastery"
    return "next_weakest"
