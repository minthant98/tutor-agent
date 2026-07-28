import pytest
from unittest.mock import AsyncMock, patch
from app.services.narration import dashboard_narration as dn


# ---------------------------------------------------------------------------
# SYSTEM_INSTRUCTION content assertions — these validate prompt discipline
# so the LLM actually receives the guard rules
# ---------------------------------------------------------------------------


def test_system_instruction_lists_banned_praise_phrases():
    """Prompt must explicitly ban praise phrases so the LLM sees them."""
    s = dn.SYSTEM_INSTRUCTION.lower()
    for banned in ["great job", "well done", "amazing", "keep it up", "you're crushing"]:
        assert banned in s, f"SYSTEM_INSTRUCTION must ban '{banned}'"


def test_system_instruction_forbids_speculation():
    s = dn.SYSTEM_INSTRUCTION.lower()
    assert "never speculate" in s or "no speculation" in s


def test_system_instruction_requires_why_explanation():
    s = dn.SYSTEM_INSTRUCTION.lower()
    assert "explain why" in s or "always explain" in s
    assert "evidence" in s or "observed data" in s


def test_system_instruction_forbids_student_name():
    s = dn.SYSTEM_INSTRUCTION.lower()
    assert "student's name" in s or "do not use the student" in s


def test_system_instruction_forbids_exclamation():
    s = dn.SYSTEM_INSTRUCTION.lower()
    assert "exclamation" in s


# ---------------------------------------------------------------------------
# Structural / wiring assertions — verify generate() actually passes the
# SYSTEM_INSTRUCTION through so no future refactor silently drops it
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_passes_system_instruction_to_llm():
    """Guard against regression: generate() must invoke llm.generate with SYSTEM_INSTRUCTION."""
    ctx = {
        "recent_grades": [],
        "mastery_trend": {"prev_mastery": 0.0, "current_mastery": 0.0, "trend": "flat"},
        "session_plan": [],
        "target_grade": "A",
    }
    with patch.object(dn.llm, "generate", new=AsyncMock(return_value="stub")) as m:
        await dn.generate(ctx)
    m.assert_called_once()
    kwargs = m.call_args.kwargs
    assert kwargs.get("system") == dn.SYSTEM_INSTRUCTION, "SYSTEM_INSTRUCTION not passed through"


@pytest.mark.asyncio
async def test_generate_includes_context_in_prompt():
    """The user message must contain the context dict so LLM can reference it."""
    ctx = {
        "recent_grades": [{"grade_pct": 62, "topic": "integration_basics", "days_ago": 1}],
        "mastery_trend": {"prev_mastery": 0.55, "current_mastery": 0.60, "trend": "up"},
        "session_plan": [{"intent": "reinforce", "topic": "integration_basics", "why": "rebuild"}],
        "target_grade": "A",
    }
    with patch.object(dn.llm, "generate", new=AsyncMock(return_value="stub")) as m:
        await dn.generate(ctx)
    prompt_arg = m.call_args.args[0] if m.call_args.args else m.call_args.kwargs.get("prompt")
    assert "integration_basics" in prompt_arg
    assert "62" in prompt_arg


@pytest.mark.asyncio
async def test_generate_fresh_student_passes_zero_mastery_in_context():
    """For a fresh student the context dict must reach the LLM with current_mastery 0.0."""
    ctx = {
        "recent_grades": [],
        "mastery_trend": {"prev_mastery": 0.0, "current_mastery": 0.0, "trend": "flat"},
        "session_plan": [{"intent": "assess", "topic": t, "why": "baseline"} for t in ["a", "b", "c"]],
        "target_grade": "A",
    }
    with patch.object(dn.llm, "generate", new=AsyncMock(return_value="stub")) as m:
        await dn.generate(ctx)
    prompt_arg = m.call_args.args[0] if m.call_args.args else m.call_args.kwargs.get("prompt")
    # The serialized context must carry the zero-mastery values
    assert "0.0" in prompt_arg
    assert "current_mastery" in prompt_arg
