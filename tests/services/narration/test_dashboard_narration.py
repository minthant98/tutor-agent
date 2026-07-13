import pytest
from unittest.mock import AsyncMock, patch
from app.services.narration import dashboard_narration


@pytest.mark.asyncio
async def test_narration_never_praises():
    ctx = {
        "recent_grades": [{"grade_pct": 62, "topic": "integration_basics", "days_ago": 1}],
        "mastery_trend": {"prev_mastery": 0.55, "current_mastery": 0.60, "trend": "up"},
        "session_plan": [{"intent": "reinforce", "topic": "integration_basics", "why": "rebuild substitution"}],
        "target_grade": "A",
    }
    with patch.object(
        dashboard_narration.llm,
        "generate",
        new=AsyncMock(return_value="Method selection stabilized. Today moves you into mixed-topic questions."),
    ):
        result = await dashboard_narration.generate(ctx)
    banned = ["great job", "well done", "amazing", "keep it up", "you're crushing", "!"]
    lower = result.lower()
    for b in banned:
        assert b not in lower, f"praise phrase {b!r} leaked into narration"


@pytest.mark.asyncio
async def test_narration_explains_why():
    ctx = {
        "recent_grades": [{"grade_pct": 40, "topic": "integration_basics", "days_ago": 1}],
        "mastery_trend": {"prev_mastery": 0.55, "current_mastery": 0.48, "trend": "down"},
        "session_plan": [{"intent": "teach", "topic": "integration_basics", "why": "rebuild +C habit"}],
        "target_grade": "A",
    }
    with patch.object(
        dashboard_narration.llm,
        "generate",
        new=AsyncMock(
            return_value="Recent Integration accuracy dropped 12%. Today rebuilds the +C habit before we move on."
        ),
    ):
        result = await dashboard_narration.generate(ctx)
    assert any(w in result.lower() for w in ["because", "since", "targets", "rebuilds", "moves you", "focuses"])


@pytest.mark.asyncio
async def test_narration_fresh_student_baseline():
    ctx = {
        "recent_grades": [],
        "mastery_trend": {"prev_mastery": 0.0, "current_mastery": 0.0, "trend": "flat"},
        "session_plan": [{"intent": "assess", "topic": t, "why": "baseline"} for t in ["a", "b", "c"]],
        "target_grade": "A",
    }
    with patch.object(
        dashboard_narration.llm,
        "generate",
        new=AsyncMock(
            return_value="You just finished onboarding. Today's a baseline assessment across your topics."
        ),
    ):
        result = await dashboard_narration.generate(ctx)
    assert "baseline" in result.lower()
