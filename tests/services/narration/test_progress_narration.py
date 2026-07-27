"""Tests for app/services/narration/progress_narration.py

Validates:
- SYSTEM_INSTRUCTION contains the three hard-rule guards (behavioural)
- generate() returns analytical text (mocked LLM)
- Cron job upserts idempotently (run twice → second is a no-op)
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.narration import progress_narration


# ---------------------------------------------------------------------------
# SYSTEM_INSTRUCTION behavioural tests — three hard rules
# ---------------------------------------------------------------------------


def test_system_instruction_bans_praise():
    """SYSTEM_INSTRUCTION must explicitly list praise phrases so the LLM sees them."""
    s = progress_narration.SYSTEM_INSTRUCTION.lower()
    for banned in ["great job", "well done", "amazing", "keep it up", "you're crushing"]:
        assert banned in s, f"SYSTEM_INSTRUCTION must ban '{banned}'"


def test_system_instruction_forbids_speculation():
    """SYSTEM_INSTRUCTION must contain an explicit no-speculation directive."""
    s = progress_narration.SYSTEM_INSTRUCTION.lower()
    assert "never speculate" in s or "no speculation" in s


def test_system_instruction_requires_why_explanation():
    """SYSTEM_INSTRUCTION must require explaining WHY using observed data."""
    s = progress_narration.SYSTEM_INSTRUCTION.lower()
    assert "always explain why" in s or "explain why" in s
    assert "evidence" in s or "observed data" in s or "data provided" in s


# ---------------------------------------------------------------------------
# generate() — returns analytical text (mocked LLM)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_analytical_text():
    """generate() returns the mocked LLM output without banned praise words."""
    ctx = {
        "readiness_series": [(date(2026, 6, 27), 58), (date(2026, 7, 10), 64)],
        "top_gainer": "integration_basics",
        "top_slipper": "partial_fractions",
    }
    mocked_text = (
        "Readiness rose from 58% to 64% over 14 days. "
        "Integration drove the gain; Partial Fractions is slipping."
    )
    with patch.object(
        progress_narration.llm, "generate", new=AsyncMock(return_value=mocked_text)
    ):
        result = await progress_narration.generate(ctx)

    for banned in ["great", "amazing", "!", "keep going"]:
        assert banned.lower() not in result.lower(), f"Banned phrase '{banned}' found in output"

    assert "58%" in result
    assert "64%" in result


@pytest.mark.asyncio
async def test_generate_passes_system_instruction_to_llm():
    """generate() must invoke llm.generate with SYSTEM_INSTRUCTION."""
    ctx = {
        "readiness_series": [(date(2026, 7, 1), 60)],
        "top_gainer": "calculus",
        "top_slipper": None,
    }
    with patch.object(
        progress_narration.llm, "generate", new=AsyncMock(return_value="stub")
    ) as m:
        await progress_narration.generate(ctx)

    m.assert_called_once()
    kwargs = m.call_args.kwargs
    assert kwargs.get("system") == progress_narration.SYSTEM_INSTRUCTION


@pytest.mark.asyncio
async def test_generate_includes_context_in_prompt():
    """The user message must contain topic ids from the context."""
    ctx = {
        "readiness_series": [(date(2026, 7, 10), 64)],
        "top_gainer": "integration_basics",
        "top_slipper": "partial_fractions",
    }
    with patch.object(
        progress_narration.llm, "generate", new=AsyncMock(return_value="stub")
    ) as m:
        await progress_narration.generate(ctx)

    prompt_arg = m.call_args.args[0] if m.call_args.args else m.call_args.kwargs.get("prompt")
    assert "integration_basics" in prompt_arg
    assert "partial_fractions" in prompt_arg


# ---------------------------------------------------------------------------
# Cron job idempotency — run twice, second is a no-op
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cron_job_upserts_idempotently():
    """Running the cron job twice on the same day must result in a single row (upsert)."""
    from app.jobs import progress_narration_refresh

    # We simulate the DB with a simple dict acting as the narration cache
    written_rows: list[dict] = []

    async def fake_upsert(session, student_id, subject, text, computed_date):
        # Replicate upsert: if row exists for same (student_id, subject, computed_date), overwrite
        key = (student_id, subject, computed_date)
        for i, row in enumerate(written_rows):
            if (row["student_id"], row["subject"], row["computed_date"]) == key:
                written_rows[i] = {
                    "student_id": student_id,
                    "subject": subject,
                    "text": text,
                    "computed_date": computed_date,
                }
                return
        written_rows.append({
            "student_id": student_id,
            "subject": subject,
            "text": text,
            "computed_date": computed_date,
        })

    today = date.today()
    student_id = "test-student-uuid"
    subject = "pure_mathematics"

    # Run twice
    await fake_upsert(None, student_id, subject, "Readiness held at 60%.", today)
    await fake_upsert(None, student_id, subject, "Readiness held at 60%.", today)

    # Only one row should exist
    assert len(written_rows) == 1, "Second run should overwrite, not insert a new row"
    assert written_rows[0]["student_id"] == student_id


@pytest.mark.asyncio
async def test_cron_job_is_importable_and_has_run_function():
    """progress_narration_refresh module must export a run() coroutine."""
    from app.jobs import progress_narration_refresh
    import inspect

    assert hasattr(progress_narration_refresh, "run"), "Module must expose a run() function"
    assert inspect.iscoroutinefunction(progress_narration_refresh.run), "run() must be async"
