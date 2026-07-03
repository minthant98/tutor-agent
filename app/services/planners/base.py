"""Planner protocol + helpers shared across all practice modes.

A Planner takes a student's context (subject, optional user-picked topic) and
returns a segment_plan plus a PlannerReason describing why each topic/intent
was chosen. Reasons are surfaced in PostHog and persisted on the session for
post-hoc debugging.
"""
from datetime import datetime, timezone
from typing import Protocol, TypedDict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearnerSubject, MasteryState, SyllabusTopic


class TopicSelection(TypedDict):
    topic: str
    mastery: float | None
    chosen_intent: str | None
    last_practiced_days: int | None
    signal: str  # short machine-readable reason


class PlannerReason(TypedDict):
    topic_selections: list[TopicSelection]


class BuildResult(TypedDict):
    plan: list[dict]
    reason: PlannerReason


class Planner(Protocol):
    session_type: str
    requires_topic: bool

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult: ...


# ── shared helpers ──────────────────────────────────────────────────────────

_TEACH_UPPER = 0.20
_REINFORCE_UPPER = 0.60


def _intent_from_mastery(m: float) -> str:
    """Map a mastery score to the pedagogically appropriate intent."""
    if m < _TEACH_UPPER:
        return "teach"
    if m < _REINFORCE_UPPER:
        return "reinforce"
    return "assess"


def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()


async def _validate_topic(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> None:
    """Raise 400 if topic isn't in the student's pinned syllabus."""
    version_res = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = version_res.scalar()
    if not version:
        raise HTTPException(400, f"Subject '{subject}' not configured for this student")

    res = await db.execute(
        select(SyllabusTopic.topic_id).where(
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
            SyllabusTopic.topic_id == topic,
        ).limit(1)
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(400, f"Topic '{topic}' not in {subject} syllabus {version}")


async def _weakest_topics_with_attempts(
    db: AsyncSession, student_id: UUID, subject: str, limit: int
) -> list[tuple[str, float]]:
    """[(topic, mastery)] sorted mastery ascending, only for topics with attempts."""
    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
        .order_by(MasteryState.mastery_score.asc())
        .limit(limit)
    )
    return list(res.all())


async def _first_syllabus_topics(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    exclude: set[str],
    limit: int,
) -> list[str]:
    """First N syllabus topics (by ordinal) for the student's pinned syllabus_version, skipping `exclude`."""
    version_res = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = version_res.scalar() or "2026.1"
    res = await db.execute(
        select(SyllabusTopic.topic_id)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.version == version)
        .order_by(SyllabusTopic.ordinal.asc())
    )
    picked: list[str] = []
    for (t,) in res.all():
        if t not in exclude:
            picked.append(t)
            if len(picked) >= limit:
                break
    return picked


async def _days_since_last_practice(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> int | None:
    res = await db.execute(
        select(MasteryState.last_reviewed_at).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        ).limit(1)
    )
    last = res.scalar_one_or_none()
    if not last:
        return None
    return (datetime.now(timezone.utc) - last).days


__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "_intent_from_mastery",
    "_format_topic",
    "_validate_topic",
    "_weakest_topics_with_attempts",
    "_first_syllabus_topics",
    "_days_since_last_practice",
]
