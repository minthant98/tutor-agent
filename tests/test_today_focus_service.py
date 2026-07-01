"""Tests for today_focus_service: shape selector and build_segment_plan."""
import pytest
from app.services import today_focus_service as svc


def test_select_shape_onboarding_when_few_sessions():
    assert svc.select_shape({"sessions_count": 0, "readiness_pct": 0, "days_until_exam": 100, "avg_mastery_trend_7d": 0}) == "onboarding"
    assert svc.select_shape({"sessions_count": 2, "readiness_pct": 30, "days_until_exam": 100, "avg_mastery_trend_7d": 0}) == "onboarding"


def test_select_shape_exam_ready_when_close_and_high_readiness():
    assert svc.select_shape({"sessions_count": 50, "readiness_pct": 80, "days_until_exam": 10, "avg_mastery_trend_7d": 0.05}) == "exam_ready"


def test_select_shape_build_when_struggling():
    assert svc.select_shape({"sessions_count": 20, "readiness_pct": 30, "days_until_exam": 100, "avg_mastery_trend_7d": -0.1}) == "build"


def test_select_shape_default_otherwise():
    assert svc.select_shape({"sessions_count": 20, "readiness_pct": 55, "days_until_exam": 60, "avg_mastery_trend_7d": 0.02}) == "default"


@pytest.mark.asyncio
async def test_build_plan_default_shape_three_segments(db_session, student, syllabus_edexcel_seeded):
    plan, reasoning = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "default")
    assert len(plan) == 3
    intents = [s["intent"] for s in plan]
    assert intents == ["revise", "reinforce", "consolidate"]
    for seg in plan:
        assert seg["why"]  # all segments have a why string


@pytest.mark.asyncio
async def test_build_plan_onboarding_shape_three_segments(db_session, student, syllabus_edexcel_seeded):
    plan, reasoning = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "onboarding")
    assert len(plan) == 3
    intents = [s["intent"] for s in plan]
    assert intents == ["teach", "teach", "assess"]
    for seg in plan:
        assert seg["why"]


@pytest.mark.asyncio
async def test_build_plan_build_shape_three_segments(db_session, student, syllabus_edexcel_seeded):
    plan, reasoning = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "build")
    assert len(plan) == 3
    intents = [s["intent"] for s in plan]
    assert intents == ["teach", "reinforce", "revise"]
    for seg in plan:
        assert seg["why"]


@pytest.mark.asyncio
async def test_build_plan_exam_ready_shape_three_segments(db_session, student, syllabus_edexcel_seeded):
    plan, reasoning = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "exam_ready")
    assert len(plan) == 3
    intents = [s["intent"] for s in plan]
    assert intents == ["assess", "consolidate", "revise"]
    for seg in plan:
        assert seg["why"]


@pytest.mark.asyncio
async def test_segment_has_required_fields(db_session, student, syllabus_edexcel_seeded):
    plan, _ = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "default")
    required_fields = {"idx", "intent", "handler", "topic", "why", "target_minutes", "status", "config"}
    for seg in plan:
        assert required_fields.issubset(set(seg.keys())), f"Missing fields in segment: {set(seg.keys())}"


def test_why_templates_cover_all_intents():
    expected_intents = {"diagnose", "teach", "reinforce", "assess", "revise", "consolidate"}
    assert expected_intents == set(svc.WHY_TEMPLATES.keys())
