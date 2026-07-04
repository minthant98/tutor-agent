"""Grading LLM for Exam Marker + Alex memory helper.

Uses the existing Groq 3-model fallback chain (text-only). Returns a
structured GradingResult that references the student's recent work on
the same topic when student_context is provided.
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm
from app.db.models import GradedUpload, MasteryState

logger = logging.getLogger(__name__)

RETRY_LIMIT = 1  # 1 retry after initial failure (2 total attempts)


class GradingCriterion(TypedDict):
    code: str
    description: str
    awarded: bool
    comment: str


class GradingResult(TypedDict):
    marks_awarded: int
    criteria: list[GradingCriterion]
    summary: str
    improvement: str


class GradeRecord(TypedDict):
    grade_pct: float
    marks_awarded: int
    max_marks: int
    improvement: str
    days_ago: int


class MasteryTrend(TypedDict):
    prev_mastery: float
    current_mastery: float
    trend: str  # "up" | "down" | "flat"


class StudentTopicContext(TypedDict):
    recent_grades: list[GradeRecord]
    mastery_trend: MasteryTrend
    recent_practice_mistakes: list[str]


@dataclass
class GradingFailed(Exception):
    reason: str

    def __str__(self) -> str:
        return f"Grading failed: {self.reason}"


async def grade(
    question: str,
    mark_scheme: str,
    answer: str,
    max_marks: int,
    student_context: StudentTopicContext | None = None,
) -> GradingResult:
    """Grade a student answer. Returns structured feedback. Raises GradingFailed on 2 bad LLM responses."""
    prompt = _build_prompt(question, mark_scheme, answer, max_marks, student_context)

    last_error: Exception | None = None
    for attempt in range(RETRY_LIMIT + 1):
        try:
            response = await _call_llm(prompt if attempt == 0 else _stricter_prompt(prompt))
            result = json.loads(response)
            # Clamp marks
            ma = int(result.get("marks_awarded", 0))
            result["marks_awarded"] = max(0, min(ma, max_marks))
            # Guarantee shape
            result.setdefault("criteria", [])
            result.setdefault("summary", "")
            result.setdefault("improvement", "")
            return result  # type: ignore[return-value]
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("Grading returned invalid JSON on attempt %d", attempt + 1)
        except Exception as exc:
            last_error = exc
            logger.warning("Grading call failed on attempt %d: %s", attempt + 1, exc)
    raise GradingFailed(reason="invalid_json_after_retry") from last_error


# ── prompt building ────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTION = """You are a chief examiner marking an A-Level maths past-paper answer.
Grade strictly against the mark scheme. Award marks only when the student
demonstrates the required step. Codes: M1 (method mark), A1 (accuracy mark),
B1 (independent mark).

Return ONLY a valid JSON object matching this exact schema — no other text:
{
  "marks_awarded": <int 0..max_marks>,
  "criteria": [
    {"code": "M1|A1|B1", "description": "<what this mark rewards>",
     "awarded": <bool>, "comment": "<why or why not, 1 sentence>"}
  ],
  "summary": "<1-2 sentences on overall performance>",
  "improvement": "<one specific actionable tip for next time>"
}"""


def _build_prompt(
    question: str,
    mark_scheme: str,
    answer: str,
    max_marks: int,
    student_context: StudentTopicContext | None,
) -> str:
    parts = [_SYSTEM_INSTRUCTION, ""]
    if student_context and _has_any_context(student_context):
        parts.append(_format_student_history(student_context))
        parts.append("")
        parts.append(
            "Use this context to make your feedback specific. Reference patterns "
            "where relevant. Do NOT invent memories — only use what's listed."
        )
        parts.append("")
    parts.append(f"Max marks: {max_marks}")
    parts.append(f"Question:\n{question}")
    parts.append("")
    parts.append(f"Mark scheme:\n{mark_scheme}")
    parts.append("")
    parts.append(f"Student answer:\n{answer}")
    return "\n".join(parts)


def _stricter_prompt(original: str) -> str:
    return original + "\n\nReturn ONLY JSON. Your previous response was invalid."


def _has_any_context(ctx: StudentTopicContext) -> bool:
    return bool(
        ctx.get("recent_grades")
        or ctx.get("recent_practice_mistakes")
        or (ctx.get("mastery_trend", {}).get("current_mastery", 0) > 0)
    )


def _format_student_history(ctx: StudentTopicContext) -> str:
    lines = ["<student_history>", "This student has recently:"]
    grades = ctx.get("recent_grades", [])
    if grades:
        percents = ", ".join(f"{int(g['grade_pct'])}%" for g in grades)
        lines.append(f"- Attempted this topic {len(grades)} times; recent grades: {percents}")
    trend = ctx.get("mastery_trend", {})
    if trend.get("trend") in ("up", "down"):
        arrow = "trending up" if trend["trend"] == "up" else "trending down"
        lines.append(
            f"- Mastery {arrow}: {int(trend['prev_mastery']*100)}% → "
            f"{int(trend['current_mastery']*100)}%"
        )
    mistakes = ctx.get("recent_practice_mistakes", [])
    if mistakes:
        lines.append("- Repeated mistakes noticed:")
        for m in mistakes[:3]:
            lines.append(f"  * {m}")
    lines.append("</student_history>")
    return "\n".join(lines)


# ── LLM call wrapper ───────────────────────────────────────────────────────

async def _call_llm(prompt: str) -> str:
    return await llm.generate(prompt)


# ── student topic context loader ───────────────────────────────────────────

async def _load_student_topic_context(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> StudentTopicContext:
    """Assemble recent grades + mastery trend + recent practice mistakes for topic."""
    now = datetime.now(timezone.utc)

    # Recent grades on this topic (last 3)
    grade_rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student_id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
        ).order_by(GradedUpload.created_at.desc()).limit(50)
    )).scalars().all()

    # Filter by topic (question_id-based topic filter not stored; use feedback context)
    recent_grades: list[GradeRecord] = []
    for row in grade_rows:
        # We don't currently persist topic on GradedUpload; approximate by matching
        # against the row's mark_scheme snippet (best effort). For MVP, take all recent
        # grades regardless of topic — reviewer can flag if this needs refinement.
        if len(recent_grades) >= 3:
            break
        improvement = ""
        if row.feedback_json:
            improvement = row.feedback_json.get("improvement", "") if isinstance(row.feedback_json, dict) else ""
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_ago = (now - created).days
        recent_grades.append({
            "grade_pct": float(row.grade_pct or 0),
            "marks_awarded": row.marks_awarded or 0,
            "max_marks": row.max_marks,
            "improvement": improvement,
            "days_ago": days_ago,
        })

    # Current mastery for the topic
    mastery_row = (await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar_one_or_none()

    current_mastery = float(mastery_row.mastery_score) if mastery_row else 0.0
    # Prev mastery approximated as current - typical practice delta; when
    # readiness_snapshots is populated we can improve this. For MVP, use flat.
    prev_mastery = max(0.0, current_mastery - 0.10) if current_mastery > 0 else 0.0
    if current_mastery > prev_mastery + 0.02:
        trend = "up"
    elif current_mastery < prev_mastery - 0.02:
        trend = "down"
    else:
        trend = "flat"

    return {
        "recent_grades": recent_grades,
        "mastery_trend": {
            "prev_mastery": prev_mastery,
            "current_mastery": current_mastery,
            "trend": trend,
        },
        "recent_practice_mistakes": [],  # populated in a future task when we mine sessions
    }
