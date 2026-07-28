"""Marker v3 Alex narration.

Enforces three hard prompt rules (constraints from spec Section 3):
1. Never praise
2. Never speculate
3. Always explain WHY today's question was chosen (evidence-driven)
"""
import json
from app.core.llm import llm

SYSTEM_INSTRUCTION = """You are Alex, an A-Level tutor speaking to a student on their exam marker landing page.

Write ONE line — 1-3 sentences maximum — introducing the suggested question and why it was chosen.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it". Use analytical language only.
2. NEVER speculate. Every claim must reference the observed data (recent grade %, weak topic, submission count).
3. ALWAYS explain WHY today's question exists. Point to specific evidence from the student's data.

DO NOT:
- Use exclamation marks
- Use the student's name
- Use emoji
- Be motivational
- Invent facts not in the context

Return only the narration text — no preamble, no quotes."""


async def generate(context: dict) -> str:
    """Generate a marker landing narration from the given student context dict.

    Args:
        context: dict with keys:
            - recent_grade_pct: float | None — average grade % across recent submissions
            - weak_topic: str | None — the topic targeted by today's question
            - today_submission_count: int — number of graded uploads today

    Returns:
        Narration string (1-3 sentences, analytical only).
    """
    prompt = f"""Context:
{json.dumps(context, indent=2)}

Write today's marker landing narration introducing the suggested question."""
    return await llm.generate(prompt, system=SYSTEM_INSTRUCTION)
