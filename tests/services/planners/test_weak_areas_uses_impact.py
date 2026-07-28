"""Integration test: WeakAreasPlanner ranks by impact_score, not raw mastery.

Scenario: two topics where raw-mastery ordering would yield one winner but
impact_score yields the opposite.  Since SyllabusTopic has no prereq-children
column (safe default: 0 for all topics), we differentiate via recency —
the factor that IS available from MasteryState.last_reviewed_at.

  Topic A — higher mastery (0.60) but not practised for 40 days → high impact
  Topic B — lower mastery  (0.50) but practised yesterday        → lower impact

Raw-mastery rank: B first (0.50 < 0.60)
Impact-score rank: A first (stale weakness beats fresh weakness)

The planner must pick A as segment 0.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.db.models import MasteryState
from app.services.planners.weak import WeakAreasPlanner


@pytest.mark.asyncio
async def test_higher_mastery_stale_topic_wins_over_fresh_lower_mastery(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    now = datetime.now(timezone.utc)

    db_session.add_all([
        # Topic A: higher mastery but neglected for 40 days
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="integration_basics",
            mastery_score=0.60,
            total_attempts=10,
            last_reviewed_at=now - timedelta(days=40),
        ),
        # Topic B: lower mastery but practised yesterday
        MasteryState(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            topic="differentiation_basics",
            mastery_score=0.50,
            total_attempts=6,
            last_reviewed_at=now - timedelta(days=1),
        ),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]

    # If ranking were raw mastery (asc), segment 0 = differentiation_basics (0.50).
    # With impact_score, integration_basics (0.60, stale) should rank first.
    assert plan[0]["topic"] == "integration_basics", (
        "Expected the stale higher-mastery topic to rank above the fresh lower-mastery topic; "
        "impact_score must be driving selection, not raw mastery."
    )
    assert plan[1]["topic"] == "differentiation_basics"
