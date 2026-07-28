"""Progress trend narration.

Enforces three hard prompt rules (matching the spec):
1. Never praise
2. Never speculate
3. Always explain WHY (point to concrete data)
"""
import json
from datetime import date
from typing import Optional

from app.core.llm import llm

SYSTEM_INSTRUCTION = """You are Alex, an A-Level tutor analysing a student's progress trend.

Write ONE analytical sentence — 2-3 sentences maximum — summarising the readiness trend and key topic drivers.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it", "fantastic", "excellent". Use analytical language only.
2. NEVER speculate. Every claim must reference the observed data (readiness series, mastery changes). Do not invent predictions or assumptions.
3. ALWAYS explain WHY. Point to specific evidence — which topic drove the gain or the slippage — using the data provided.

DO NOT:
- Use exclamation marks
- Use the student's name
- Use emoji
- Be motivational or encouraging
- Invent facts not in the context

EXAMPLE OUTPUT:
Readiness rose from 58% to 64% over 14 days. Integration drove the gain; Partial Fractions is slipping.

Return only the narration text — no preamble, no quotes."""


async def generate(context: dict) -> str:
    """Generate a progress trend narration from the given context dict.

    Args:
        context: dict with keys:
            - readiness_series: list of (date, pct) tuples covering last 14 days
            - top_gainer: topic id with highest mastery gain in the period
            - top_slipper: topic id with lowest mastery change (may be None)

    Returns:
        Narration string (2-3 sentences, analytical only, max 500 chars).
    """
    # Serialise dates to strings for JSON
    serialisable_series = [
        (d.isoformat() if isinstance(d, date) else str(d), pct)
        for d, pct in context.get("readiness_series", [])
    ]
    ctx_payload = {
        **context,
        "readiness_series": serialisable_series,
    }

    prompt = f"""Progress context:
{json.dumps(ctx_payload, indent=2)}

Write the progress trend narration."""
    return await llm.generate(prompt, system=SYSTEM_INSTRUCTION)
