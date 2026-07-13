"""Dashboard Alex narration.

Enforces three hard prompt rules (constraints from spec Section 3):
1. Never praise
2. Never speculate
3. Always explain WHY today's plan exists
"""
import json
from app.core.llm import llm

SYSTEM_INSTRUCTION = """You are Alex, an A-Level tutor speaking to a student on their dashboard.

Write ONE line — 1-3 sentences maximum — introducing today's session plan.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it". Use analytical language only.
2. NEVER speculate. Every claim must reference the observed data (grades, mastery trend, session plan).
3. ALWAYS explain WHY today's plan exists. Point to specific evidence from the student's data.

DO NOT:
- Use exclamation marks
- Use the student's name
- Use emoji
- Be motivational
- Invent facts not in the context

Return only the narration text — no preamble, no quotes."""


async def generate(context: dict) -> str:
    """Generate a dashboard narration from the given student context dict.

    Args:
        context: dict with keys:
            - recent_grades: list of {grade_pct, topic, days_ago}
            - mastery_trend: {prev_mastery, current_mastery, trend}
            - session_plan: list of {intent, topic, why}
            - target_grade: str

    Returns:
        Narration string (1-3 sentences, analytical only).
    """
    prompt = f"""Context:
{json.dumps(context, indent=2)}

Write today's dashboard narration."""
    return await llm.generate(prompt, system=SYSTEM_INSTRUCTION)
