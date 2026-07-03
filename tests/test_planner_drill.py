import pytest
from app.services.planners.drill import DrillInPlanner


def test_drill_planner_metadata():
    p = DrillInPlanner()
    assert p.session_type == "drill_in"
    assert p.requires_topic is True


@pytest.mark.asyncio
async def test_drill_planner_produces_3_segments_same_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    plan = result["plan"]
    assert len(plan) == 3
    for seg in plan:
        assert seg["topic"] == "integration_basics"
        assert seg["handler"] == "practice"
    assert [s["intent"] for s in plan] == ["teach", "reinforce", "assess"]
    assert [s["target_minutes"] for s in plan] == [4, 4, 2]
    assert [s["config"]["allow_hints"] for s in plan] == [True, True, False]
    assert plan[0]["status"] == "in_progress"
    assert plan[1]["status"] == "pending"
    assert plan[2]["status"] == "pending"


@pytest.mark.asyncio
async def test_drill_planner_reason_signal(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 1
    assert sel[0]["signal"] == "drill_in_from_dashboard"


@pytest.mark.asyncio
async def test_drill_planner_first_segment_has_worked_example_addendum(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    assert "worked example" in result["plan"][0]["config"]["system_prompt_addendum"].lower()
