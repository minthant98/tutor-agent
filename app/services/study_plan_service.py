import json
import logging
from datetime import date

from app.core.llm import llm, LLMError

logger = logging.getLogger(__name__)

_SYLLABUS_TOPICS: dict[str, list[str]] = {
    "pure_mathematics": [
        "Algebra and functions", "Coordinate geometry", "Sequences and series",
        "Trigonometry", "Exponentials and logarithms", "Differentiation",
        "Integration", "Numerical methods", "Vectors", "Proof",
        "Binomial expansion", "Parametric equations", "Differential equations",
        "Partial fractions",
    ],
    "mathematics": [
        "Pure 1: Quadratics and functions", "Pure 1: Coordinate geometry",
        "Pure 1: Circular measure", "Pure 1: Trigonometry", "Pure 1: Series",
        "Pure 1: Differentiation", "Pure 1: Integration",
        "Pure 2: Algebra", "Pure 2: Logarithms", "Pure 2: Trigonometry",
        "Pure 2: Differentiation", "Pure 2: Integration",
        "Pure 2: Numerical methods", "Pure 2: Differential equations",
        "Pure 2: Vectors",
    ],
}

_DEFAULT_TOPICS = [
    "Algebra", "Functions", "Calculus", "Trigonometry",
    "Statistics", "Mechanics", "Proof",
]


def _weeks_until(exam_date: date | None) -> int:
    if not exam_date:
        return 8
    delta = (exam_date - date.today()).days
    return max(1, delta // 7)


async def generate_plan(
    subject: str,
    exam_board: str,
    exam_date: date | None,
    weak_topics: list[str],
) -> list[dict]:
    weeks = _weeks_until(exam_date)
    all_topics = _SYLLABUS_TOPICS.get(subject, _DEFAULT_TOPICS)

    prompt = f"""You are an expert {exam_board.upper()} A-Level {subject.replace("_", " ").title()} tutor.

Create a {weeks}-week study plan for a student.

Student profile:
- Weak topics (prioritise these): {", ".join(weak_topics) if weak_topics else "not yet identified"}
- Weeks until exam: {weeks}
- All syllabus topics: {", ".join(all_topics)}

Rules:
- Cover ALL syllabus topics across the {weeks} weeks
- Put weak topics in the first half of the plan
- Each week should have 2-4 topics
- The "focus" field is one motivating sentence about why that week's topics matter in the exam
- Balance workload evenly across weeks

Return a JSON array with exactly {weeks} objects, each with:
  "week": integer (1 to {weeks})
  "topics": array of topic name strings
  "focus": one sentence string

Return only the JSON array, no other text."""

    try:
        raw = await llm.generate_json(prompt)
        if isinstance(raw, list):
            return raw
        return raw.get("plan", raw.get("weeks", []))
    except (LLMError, json.JSONDecodeError, AttributeError) as e:
        logger.error("Study plan generation failed: %s", e)
        # Fallback: evenly distribute topics
        return _fallback_plan(all_topics, weak_topics, weeks)


def _fallback_plan(all_topics: list[str], weak_topics: list[str], weeks: int) -> list[dict]:
    ordered = weak_topics + [t for t in all_topics if t not in weak_topics]
    chunk = max(1, len(ordered) // weeks)
    plan = []
    for i in range(weeks):
        start = i * chunk
        batch = ordered[start:start + chunk] or [ordered[-1]]
        plan.append({"week": i + 1, "topics": batch, "focus": "Build confidence and exam technique."})
    return plan
