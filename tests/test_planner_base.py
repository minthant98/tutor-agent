import pytest
from app.services.planners.base import _intent_from_mastery, _format_topic


def test_intent_from_mastery_teach_boundary():
    assert _intent_from_mastery(0.0) == "teach"
    assert _intent_from_mastery(0.19) == "teach"

def test_intent_from_mastery_reinforce_range():
    assert _intent_from_mastery(0.20) == "reinforce"
    assert _intent_from_mastery(0.35) == "reinforce"
    assert _intent_from_mastery(0.59) == "reinforce"

def test_intent_from_mastery_assess_boundary():
    assert _intent_from_mastery(0.60) == "assess"
    assert _intent_from_mastery(0.85) == "assess"
    assert _intent_from_mastery(1.0) == "assess"

def test_format_topic_snake_to_title():
    assert _format_topic("integration_basics") == "Integration Basics"
    assert _format_topic("differentiation_chain_product_quotient") == "Differentiation Chain Product Quotient"


@pytest.mark.asyncio
async def test_validate_topic_raises_when_subject_not_configured(db_session, student):
    """Student has no LearnerSubject row → 400."""
    from fastapi import HTTPException
    from app.services.planners.base import _validate_topic
    with pytest.raises(HTTPException) as exc:
        await _validate_topic(db_session, student.id, "pure_mathematics", "integration_basics")
    assert exc.value.status_code == 400
    assert "not configured" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_topic_raises_when_topic_not_in_syllabus(db_session, student_with_subject, syllabus_edexcel_seeded):
    from fastapi import HTTPException
    from app.services.planners.base import _validate_topic
    with pytest.raises(HTTPException) as exc:
        await _validate_topic(db_session, student_with_subject.id, "pure_mathematics", "not_a_real_topic")
    assert exc.value.status_code == 400
    assert "not in" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_topic_accepts_valid_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    from app.services.planners.base import _validate_topic
    # Should not raise
    await _validate_topic(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")


def test_planners_registry_is_empty_at_this_task():
    from app.services.planners import PLANNERS
    assert isinstance(PLANNERS, dict)
