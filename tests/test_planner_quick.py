import pytest
from app.services.planners.quick import QuickPlanner


def test_quick_planner_metadata():
    p = QuickPlanner()
    assert p.session_type == "quick_practice"
    assert p.requires_topic is True


@pytest.mark.asyncio
async def test_quick_planner_produces_1_segment(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = QuickPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    assert len(result["plan"]) == 1
    seg = result["plan"][0]
    assert seg["idx"] == 0
    assert seg["intent"] == "reinforce"
    assert seg["handler"] == "practice"
    assert seg["topic"] == "integration_basics"
    assert seg["target_minutes"] == 5
    assert seg["status"] == "in_progress"
    assert seg["config"]["mode"] == "quick_practice"
    assert seg["config"]["max_questions"] == 3
    assert seg["config"]["allow_hints"] is True


@pytest.mark.asyncio
async def test_quick_planner_reason_signal(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = QuickPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 1
    assert sel[0]["topic"] == "integration_basics"
    assert sel[0]["chosen_intent"] == "reinforce"
    assert sel[0]["signal"] == "user_selected"


@pytest.mark.asyncio
async def test_quick_planner_rejects_unknown_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    from fastapi import HTTPException
    p = QuickPlanner()
    with pytest.raises(HTTPException) as exc:
        await p.build(db_session, student_with_subject.id, "pure_mathematics", "not_a_topic")
    assert exc.value.status_code == 400
