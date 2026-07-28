"""3-segment plan across 2 weakest topics + mistakes review.

Adaptive intent selection: each segment's intent is derived from the topic's
current mastery via _intent_from_mastery. A near-zero-mastery topic gets a
worked example (teach), a partial-mastery topic gets repetition (reinforce),
and a solid topic gets a no-hint pressure test (assess).

Topic ranking uses a composite impact_score rather than raw mastery so that
recency (days since last practice) is factored in alongside weakness.

Note: SyllabusTopic has no `weight` or prereq-children columns as of
2026.1 schema. Safe defaults are applied:
  exam_frequency=0.1  (mild non-zero weight)
  prereq_children=0   (no downstream unlocks assumed)
"""
from datetime import datetime, timezone
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
from app.services.planners.impact_score import TopicStats, impact_score

_DEFAULT_EXAM_FREQUENCY = 0.1
_DEFAULT_PREREQ_CHILDREN = 0


async def _topics_ranked_by_impact(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    limit: int,
) -> list[tuple[str, float]]:
    """Return [(topic_id, mastery)] ordered by impact_score descending.

    Fetches all attempted topics, computes impact_score using days_since_practice
    from MasteryState.last_reviewed_at plus safe defaults for fields absent from
    the current schema (prereq_children=0, exam_frequency=0.1).
    """
    from sqlalchemy import select
    from app.db.models import MasteryState

    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score, MasteryState.last_reviewed_at)
        .where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
    )
    rows = res.all()

    now = datetime.now(timezone.utc)
    scored: list[tuple[float, str, float]] = []
    for topic_id, mastery, last_reviewed_at in rows:
        if last_reviewed_at is None:
            days = 30  # treat never-reviewed as maximally stale
        else:
            # last_reviewed_at may be offset-naive (UTC) from older rows
            lr = last_reviewed_at
            if lr.tzinfo is None:
                lr = lr.replace(tzinfo=timezone.utc)
            days = max((now - lr).days, 0)

        stats = TopicStats(
            mastery=mastery,
            days_since_practice=days,
            prereq_children=_DEFAULT_PREREQ_CHILDREN,
            exam_frequency=_DEFAULT_EXAM_FREQUENCY,
        )
        scored.append((impact_score(stats), topic_id, mastery))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(topic_id, mastery) for _, topic_id, mastery in scored[:limit]]


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
        weak = await _topics_ranked_by_impact(db, student_id, subject, limit=2)
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
