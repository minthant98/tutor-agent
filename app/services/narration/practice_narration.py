"""Practice landing Alex narration.

Enforces three hard prompt rules (constraints from spec Section 3):
1. Never praise
2. Never speculate
3. Always explain WHY these topics are the focus
"""
import json
from app.core.llm import llm

SYSTEM_INSTRUCTION = """You are Alex, an A-Level tutor speaking to a student on their practice landing page.

Write ONE line — 1-3 sentences maximum — introducing the student's current weak areas.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it". Use analytical language only.
2. NEVER speculate. Every claim must reference the observed data (mastery scores, attempt history, weak topics).
3. ALWAYS explain WHY these topics are the focus. Point to specific evidence from the student's data.

DO NOT:
- Use exclamation marks
- Use the student's name
- Use emoji
- Be motivational
- Invent facts not in the context

Return only the narration text — no preamble, no quotes."""


async def generate(context: dict) -> str:
    """Generate a practice landing narration from the given student context dict.

    Args:
        context: dict with keys:
            - weak_topics: list of {topic_id, topic_name, mastery_pct}
            - subject: str

    Returns:
        Narration string (1-3 sentences, analytical only).
    """
    prompt = f"""Context:
{json.dumps(context, indent=2)}

Write a practice landing narration introducing the student's weak areas."""
    return await llm.generate(prompt, system=SYSTEM_INSTRUCTION)
