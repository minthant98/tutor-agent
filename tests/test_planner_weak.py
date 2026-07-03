import pytest
from datetime import datetime, timezone, timedelta
from app.db.models import MasteryState
from app.services.planners.weak import WeakAreasPlanner


def test_weak_areas_metadata():
    p = WeakAreasPlanner()
    assert p.session_type == "weak_areas"
    assert p.requires_topic is False


@pytest.mark.asyncio
async def test_weak_areas_two_low_mastery_topics(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Student with 2 attempted topics at mastery 0.15 and 0.48 gets teach + reinforce + mistakes."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.15, total_attempts=3,
                     last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=21)),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.48, total_attempts=5,
                     last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=3)),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert len(plan) == 3
    # Segment 0: weakest topic (integration_basics, 0.15 → teach)
    assert plan[0]["topic"] == "integration_basics"
    assert plan[0]["intent"] == "teach"
    assert "worked example" in plan[0]["config"]["system_prompt_addendum"].lower()
    # Segment 1: next-weakest (differentiation_basics, 0.48 → reinforce)
    assert plan[1]["topic"] == "differentiation_basics"
    assert plan[1]["intent"] == "reinforce"
    # Segment 2: mistakes review
    assert plan[2]["intent"] == "consolidate"
    assert plan[2]["handler"] == "mistakes"
    assert plan[2]["topic"] is None


@pytest.mark.asyncio
async def test_weak_areas_high_mastery_becomes_assess(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Topic with mastery 0.65 becomes an 'assess' segment with hints disabled."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.65, total_attempts=8),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.30, total_attempts=4),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    # Segment 0 was picked as the weakest with attempts (differentiation_basics @ 0.30 → reinforce)
    assert plan[0]["topic"] == "differentiation_basics"
    assert plan[0]["intent"] == "reinforce"
    # Segment 1 next-weakest — integration_basics @ 0.65 → assess
    assert plan[1]["intent"] == "assess"
    assert plan[1]["config"]["allow_hints"] is False
    assert plan[1]["config"]["max_questions"] == 2


@pytest.mark.asyncio
async def test_weak_areas_fresh_student_fallback(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Student with no attempted topics gets syllabus-seeded plan, all teach intent."""
    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert len(plan) == 3
    # Both non-mistakes segments should have intent=teach (mastery=0.0 fallback)
    assert plan[0]["intent"] == "teach"
    assert plan[1]["intent"] == "teach"
    # Both topics come from the syllabus in ordinal order
    # (first two syllabus topics for Edexcel Pure Maths per syllabus_seed.py)
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_two = [t["topic_id"] for t in EDEXCEL_9MA0_TOPICS[:2]]
    assert plan[0]["topic"] == first_two[0]
    assert plan[1]["topic"] == first_two[1]

    # Both selections have signal = syllabus_seed_fallback
    sel = result["reason"]["topic_selections"]
    assert sel[0]["signal"] == "syllabus_seed_fallback"
    assert sel[1]["signal"] == "syllabus_seed_fallback"


@pytest.mark.asyncio
async def test_weak_areas_one_attempted_dedup(db_session, student_with_subject, syllabus_edexcel_seeded):
    """1 attempted topic + fallback should not repeat the attempted topic."""
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_topic = EDEXCEL_9MA0_TOPICS[0]["topic_id"]
    db_session.add(
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic=first_topic, mastery_score=0.10, total_attempts=2)
    )
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert plan[0]["topic"] == first_topic
    # Segment 1 must be a *different* topic — not first_topic again
    assert plan[1]["topic"] != first_topic


@pytest.mark.asyncio
async def test_weak_areas_reason_signals(db_session, student_with_subject, syllabus_edexcel_seeded):
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.15, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.48, total_attempts=5),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 3
    assert sel[0]["signal"] == "weakest_topic_low_mastery"
    assert sel[1]["signal"] == "next_weakest"
    assert sel[2]["signal"] == "mistakes_from_recent_sessions"
