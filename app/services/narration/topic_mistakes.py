"""
app/services/narration/topic_mistakes.py
-----------------------------------------
Generate evidence-backed mistake patterns for a specific topic from a student's
graded upload history.

Three hard rules (same as all Alex narration):
1. NEVER praise
2. NEVER speculate — every claim must reference specific evidence
3. NEVER invent — if evidence is absent, return empty list

Fresh student (no attempts) → return [] without calling LLM.
Cap at 3 items, drop any item whose evidence_submission_ids is empty (anti-hallucination guard).
"""
import json
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm
from app.db.models import GradedUpload

SYSTEM_INSTRUCTION = """You are Alex, an analytical A-Level tutor reviewing a student's submission history for a specific topic.

Identify up to 3 specific, recurring mistake patterns based ONLY on the evidence provided.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it", "good attempt", "nice work". Use analytical language only.
2. NEVER speculate. Do not invent mistakes not evidenced in the provided submissions. Every mistake pattern you identify must reference specific submission IDs from the evidence.
3. NEVER invent facts. If the evidence does not clearly show a recurring pattern, do not report one.

OUTPUT FORMAT:
Return a JSON array. Each element must have:
- "text": string — one concise analytical sentence describing the mistake pattern (max 30 words). Reference the number of attempts.
- "evidence_submission_ids": array of strings — the UUIDs of the submissions that evidence this pattern. MUST be non-empty.

If no clear recurring pattern exists, return an empty array: []

DO NOT:
- Use exclamation marks
- Use the student's name
- Use emoji
- Be motivational
- Invent submission IDs not in the provided evidence
- Return more than 3 items

Return only the JSON array — no preamble, no explanation."""


async def generate(
    db: AsyncSession,
    student_id: UUID,
    topic_id: str,
    subject: str = "",
) -> list[dict]:
    """Generate evidence-backed mistake patterns for a student on a topic.

    Args:
        db: AsyncSession
        student_id: UUID of the student
        topic_id: topic identifier string
        subject: optional subject filter (used as subject filter on GradedUpload)

    Returns:
        List of dicts with keys:
          - text: str — analytical mistake description
          - evidence_submission_ids: list[str] — non-empty list of submission UUIDs
    """
    # Query last 10 graded uploads for this student (optionally filtered by subject)
    query = (
        select(GradedUpload)
        .where(
            GradedUpload.student_id == student_id,
            GradedUpload.status == "graded",
        )
        .order_by(GradedUpload.created_at.desc())
        .limit(10)
    )
    if subject:
        query = query.where(GradedUpload.subject == subject)

    rows = (await db.execute(query)).scalars().all()

    # Fresh student — no attempts → return empty without calling LLM
    if not rows:
        return []

    # Build evidence context from feedback_json (missed criteria / improvement notes)
    evidence_items = []
    for row in rows:
        feedback = row.feedback_json if isinstance(row.feedback_json, dict) else {}
        # Extract missed criteria comments and improvement notes
        missed_criteria = feedback.get("missed_criteria", [])
        if isinstance(missed_criteria, str):
            missed_criteria = [missed_criteria]
        improvement = feedback.get("improvement", "")
        criteria_feedback = feedback.get("criteria_feedback", [])
        if isinstance(criteria_feedback, str):
            criteria_feedback = [criteria_feedback]

        # Collect all evidence text
        evidence_text_parts = []
        if missed_criteria:
            evidence_text_parts.append(f"Missed criteria: {'; '.join(str(c) for c in missed_criteria)}")
        if improvement:
            evidence_text_parts.append(f"Improvement note: {improvement}")
        if criteria_feedback:
            evidence_text_parts.append(f"Criteria feedback: {'; '.join(str(c) for c in criteria_feedback)}")
        # Also include marks for context
        marks_info = f"Marks: {row.marks_awarded}/{row.max_marks}" if row.marks_awarded is not None else f"Max marks: {row.max_marks}"

        evidence_items.append({
            "submission_id": str(row.id),
            "marks_info": marks_info,
            "evidence": " | ".join(evidence_text_parts) if evidence_text_parts else "No specific feedback recorded.",
            "question_preview": row.question_text[:80] if row.question_text else "",
        })

    # Build prompt with evidence
    prompt = f"""Topic: {topic_id}
Number of submissions reviewed: {len(evidence_items)}

Submission evidence:
{json.dumps(evidence_items, indent=2)}

Identify up to 3 recurring mistake patterns from this evidence. Return a JSON array only."""

    raw = await llm.generate(prompt, system=SYSTEM_INSTRUCTION)

    # Parse JSON response
    try:
        raw_stripped = raw.strip()
        # Extract JSON array if wrapped in markdown
        if "```" in raw_stripped:
            start = raw_stripped.find("[")
            end = raw_stripped.rfind("]") + 1
            if start != -1 and end > start:
                raw_stripped = raw_stripped[start:end]
        parsed = json.loads(raw_stripped)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, return empty — never hallucinate
        return []

    if not isinstance(parsed, list):
        return []

    # Anti-hallucination guard: drop any item with empty evidence_submission_ids
    # Also validate that submission_ids are real (present in our evidence set)
    valid_ids = {item["submission_id"] for item in evidence_items}

    result = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        text = item.get("text", "").strip()
        evidence_ids = item.get("evidence_submission_ids", [])
        if not text:
            continue
        # Must have at least one non-empty evidence ID
        if not evidence_ids:
            continue
        # Filter to only IDs that actually exist in our evidence
        filtered_ids = [eid for eid in evidence_ids if eid in valid_ids]
        if not filtered_ids:
            continue
        result.append({"text": text, "evidence_submission_ids": filtered_ids})
        if len(result) >= 3:
            break

    return result
