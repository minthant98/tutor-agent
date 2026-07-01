"""
app/services/today_focus_service.py
-------------------------------------
Today's Focus generation, caching, and persistence.

Public API
----------
select_shape(student_state: dict) -> str
build_segment_plan(db, student_id, subject, shape) -> (plan, reasoning)
get_or_generate(db, redis, student_id, subject) -> dict
invalidate_today(redis, student_id, subject) -> None
_cache_key(student_id, subject, focus_date) -> str
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    LearnerSubject,
    MasteryState,
    SyllabusTopic,
    TutorSession,
    TodayFocusHistory,
)

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "1.0"

WHY_TEMPLATES = {
    "diagnose": "Let's see where you are with {topic}.",
    "teach": "This topic is new for you — let's build it up.",
    "reinforce": "Your mastery on {topic} dropped to {pct}%. Let's bring it back up.",
    "assess": "Time to test what you've learned — no hints this round.",
    "revise": "Quick revisit of {topic} — let's lock it in.",
    "consolidate": "Reviewing concepts you've nearly mastered to make them stick.",
}


# ---------------------------------------------------------------------------
# Shape selector
# ---------------------------------------------------------------------------

def select_shape(student_state: dict) -> str:
    """
    Decide which today's-focus shape fits this student's current situation.

    Decision order (first match wins):
      1. sessions_count < 3  → "onboarding"
      2. days_until_exam <= 14 AND readiness_pct >= 75  → "exam_ready"
      3. readiness_pct < 40 OR avg_mastery_trend_7d < -0.05  → "build"
      4. otherwise  → "default"
    """
    if student_state["sessions_count"] < 3:
        return "onboarding"
    if student_state["days_until_exam"] <= 14 and student_state["readiness_pct"] >= 75:
        return "exam_ready"
    if student_state["readiness_pct"] < 40 or student_state["avg_mastery_trend_7d"] < -0.05:
        return "build"
    return "default"


# ---------------------------------------------------------------------------
# Internal DB helpers
# ---------------------------------------------------------------------------

def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()


async def _pick_topics_by_mastery(
    db: AsyncSession, student_id: UUID, subject: str
) -> list[tuple[str, float, int]]:
    """Return [(topic_id, mastery_score, total_attempts)] sorted by mastery ascending."""
    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score, MasteryState.total_attempts)
        .where(MasteryState.student_id == student_id, MasteryState.subject == subject)
        .order_by(MasteryState.mastery_score.asc())
    )
    return list(res.all())


async def _pick_next_syllabus_topic(
    db: AsyncSession, subject: str, version: str, exclude: set
) -> str | None:
    """Return the lowest-ordinal topic_id not yet in `exclude`."""
    res = await db.execute(
        select(SyllabusTopic.topic_id)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.version == version)
        .order_by(SyllabusTopic.ordinal.asc())
    )
    for (tid,) in res.all():
        if tid not in exclude:
            return tid
    return None


def _segment(idx: int, intent: str, handler: str, topic, why: str, target_minutes: int, config=None) -> dict:
    return {
        "idx": idx,
        "intent": intent,
        "handler": handler,
        "topic": topic,
        "why": why,
        "target_minutes": target_minutes,
        "status": "pending" if idx > 0 else "in_progress",
        "config": config or {},
    }


# ---------------------------------------------------------------------------
# Segment plan builder
# ---------------------------------------------------------------------------

async def build_segment_plan(
    db: AsyncSession, student_id: UUID, subject: str, shape: str
) -> tuple[list, list]:
    """
    Build a 3-segment plan for the given shape.

    Returns (plan, reasoning) where:
      plan     — list of segment dicts
      reasoning — list of {segment_idx, factors} dicts
    """
    # Look up syllabus version from LearnerSubject; fall back to 2026.1
    ls_row = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = ls_row.scalar() or "2026.1"

    mastery = await _pick_topics_by_mastery(db, student_id, subject)
    studied = {t for t, _, _ in mastery}
    weakest = mastery[0] if mastery else None

    plan: list[dict] = []

    if shape == "default":
        # Segment 0: revise weakest topic
        t1 = weakest[0] if weakest else await _pick_next_syllabus_topic(db, subject, version, studied)
        plan.append(_segment(
            0, "revise", "review", t1,
            WHY_TEMPLATES["revise"].format(topic=_format_topic(t1) if t1 else "your weakest area"),
            10,
        ))
        # Segment 1: reinforce 2nd-weakest
        t2 = mastery[1][0] if len(mastery) > 1 else await _pick_next_syllabus_topic(
            db, subject, version, studied | {t1}
        )
        pct = int((mastery[1][1] if len(mastery) > 1 else 0) * 100)
        plan.append(_segment(
            1, "reinforce", "practice", t2,
            WHY_TEMPLATES["reinforce"].format(
                topic=_format_topic(t2) if t2 else "your next topic", pct=pct
            ),
            15,
        ))
        # Segment 2: consolidate via mistakes
        plan.append(_segment(
            2, "consolidate", "mistakes", None,
            WHY_TEMPLATES["consolidate"],
            5,
        ))

    elif shape == "onboarding":
        t1 = await _pick_next_syllabus_topic(db, subject, version, studied)
        plan.append(_segment(
            0, "teach", "practice", t1,
            "Let's start with the first topic.",
            10,
            config={
                "system_prompt_addendum": "Open with a worked example before asking the student to attempt.",
                "allow_hints": True,
            },
        ))
        plan.append(_segment(
            1, "teach", "practice", t1,
            "I'll walk through a worked example.",
            10,
            config={"auto_answer": True},
        ))
        plan.append(_segment(
            2, "assess", "practice", t1,
            WHY_TEMPLATES["assess"],
            5,
            config={"allow_hints": False},
        ))

    elif shape == "build":
        t1 = (
            await _pick_next_syllabus_topic(db, subject, version, studied)
            or (weakest[0] if weakest else None)
        )
        plan.append(_segment(
            0, "teach", "practice", t1,
            "Let's build this up properly.",
            15,
            config={"system_prompt_addendum": "Open with a worked example before asking the student to attempt."},
        ))
        weak_topic = weakest[0] if weakest else t1
        weak_pct = int((weakest[1] if weakest else 0) * 100)
        plan.append(_segment(
            1, "reinforce", "practice", weak_topic,
            WHY_TEMPLATES["reinforce"].format(topic=_format_topic(weak_topic) if weak_topic else "this area", pct=weak_pct),
            10,
        ))
        plan.append(_segment(
            2, "revise", "review", weak_topic,
            WHY_TEMPLATES["revise"].format(topic=_format_topic(weak_topic) if weak_topic else "this area"),
            5,
        ))

    else:  # exam_ready
        t = weakest[0] if weakest else None
        plan.append(_segment(
            0, "assess", "practice", t,
            WHY_TEMPLATES["assess"],
            20,
            config={"time_limit_seconds": 1200},
        ))
        plan.append(_segment(
            1, "consolidate", "mistakes", None,
            WHY_TEMPLATES["consolidate"],
            10,
        ))
        plan.append(_segment(
            2, "revise", "mistakes", None,
            "Quick flash review of recent misses.",
            5,
            config={"pace": "rapid"},
        ))

    reasoning = [
        {"segment_idx": seg["idx"], "factors": {"shape": shape, "topic": seg.get("topic")}}
        for seg in plan
    ]
    return plan, reasoning


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_key(student_id, subject: str, focus_date) -> str:
    """Build cache key. focus_date may be a date object or an ISO string."""
    if hasattr(focus_date, "isoformat"):
        date_str = focus_date.isoformat()
    else:
        date_str = str(focus_date)  # already an ISO string
    return f"today_focus:{student_id}:{subject}:{date_str}"


async def _get_session_count(db: AsyncSession, student_id: UUID, subject: str) -> int:
    res = await db.execute(
        select(func.count(TutorSession.id)).where(
            TutorSession.student_id == student_id,
            TutorSession.subject == subject,
        )
    )
    return res.scalar() or 0


async def _days_until_exam(db: AsyncSession, student_id: UUID, subject: str) -> int:
    res = await db.execute(
        select(LearnerSubject.exam_date).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    exam_date = res.scalar()
    if not exam_date:
        return 180
    return max(0, (exam_date - date.today()).days)


async def _build_student_state(db: AsyncSession, student_id: UUID, subject: str) -> dict:
    from app.services.readiness_service import compute_readiness_pct
    # Determine syllabus version
    ls_row = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = ls_row.scalar() or "2026.1"
    return {
        "sessions_count": await _get_session_count(db, student_id, subject),
        "days_until_exam": await _days_until_exam(db, student_id, subject),
        "readiness_pct": await compute_readiness_pct(db, student_id, subject, version),
        "avg_mastery_trend_7d": 0.0,  # TODO: compute from snapshots when available
    }


# ---------------------------------------------------------------------------
# Main entry point: get_or_generate
# ---------------------------------------------------------------------------

def get_or_generate_sync(redis, student_id, subject: str, db_result: dict) -> dict | None:
    """Internal: check cache synchronously and return cached payload or None."""
    today = date.today()
    key = _cache_key(student_id, subject, today)
    cached = redis.get(key)
    if cached:
        return json.loads(cached if isinstance(cached, str) else cached.decode())
    return None


async def get_or_generate(db: AsyncSession, redis, student_id, subject: str) -> dict:
    """
    Return today's focus plan for this student+subject.

    1. Check Redis cache — return immediately on hit.
    2. Acquire idempotency lock (nx=True, ex=30s) — poll briefly if another
       writer already holds the lock.
    3. Build student state, select shape, build segment plan.
    4. Persist to today_focus_history (upsert via flush; duplicate is handled
       by the DB unique constraint — ignored on second call).
    5. Write to Redis with TTL until midnight UTC.
    6. Return payload dict.
    """
    today = date.today()
    key = _cache_key(student_id, subject, today)

    # Cache hit
    cached = redis.get(key)
    if cached:
        return json.loads(cached if isinstance(cached, str) else cached.decode())

    # Idempotency lock — prevent dual-device generation race
    lock_key = f"{key}:lock"
    got_lock = redis.set(lock_key, "1", nx=True, ex=30)
    if not got_lock:
        # Another writer is generating; poll briefly
        import time
        for _ in range(20):
            cached = redis.get(key)
            if cached:
                return json.loads(cached if isinstance(cached, str) else cached.decode())
            time.sleep(0.1)

    # Build plan
    state = await _build_student_state(db, student_id, subject)
    shape = select_shape(state)
    plan, reasoning = await build_segment_plan(db, student_id, subject, shape)

    expires = datetime.combine(
        today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )
    now_utc = datetime.now(timezone.utc)
    payload = {
        "shape": shape,
        "segment_plan": plan,
        "reasoning": reasoning,
        "generator_version": GENERATOR_VERSION,
        "generated_at": now_utc.isoformat(),
        "expires_at": expires.isoformat(),
        "focus_date": today.isoformat(),
    }

    # Persist to history (ignore UniqueConstraint on duplicate — already generated today)
    try:
        db.add(TodayFocusHistory(
            student_id=student_id,
            subject=subject,
            focus_date=today,
            generator_version=GENERATOR_VERSION,
            shape=shape,
            segment_plan=plan,
            reasoning=reasoning,
            expires_at=expires,
        ))
        await db.flush()
    except Exception:
        # Unique constraint violation means it was already persisted (race condition)
        await db.rollback()
        # Re-check cache after rollback — the race winner may have written it
        cached = redis.get(key)
        if cached:
            return json.loads(cached if isinstance(cached, str) else cached.decode())

    ttl_sec = max(1, int((expires - now_utc).total_seconds()))
    redis.set(key, json.dumps(payload, default=str), ex=ttl_sec)

    try:
        from app.core.telemetry import capture
        capture(str(student_id), "today_focus_generated", {
            "shape": shape,
            "intents": [s["intent"] for s in plan],
            "topics": [s["topic"] for s in plan],
            "generator_version": GENERATOR_VERSION,
        })
    except Exception:
        pass

    return payload


def invalidate_today(redis, student_id, subject: str) -> None:
    """Delete the Redis cache key for today's focus (forces regeneration on next call)."""
    redis.delete(_cache_key(student_id, subject, date.today()))
