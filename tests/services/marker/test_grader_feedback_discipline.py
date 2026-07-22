"""Behavioral tests for grader LLM prompt discipline (Task 25).

These tests verify that:
1. The grader prompt encodes the what-happened / why / what-next discipline
2. The _load_student_topic_context helper sorts grades most-recent-first (DESC)
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.marker import grader_llm
from app.db.models import GradedUpload


# ── Prompt discipline tests (no DB needed — purely unit) ──────────────────────

def test_grader_prompt_encodes_what_why_next():
    """SYSTEM_INSTRUCTION must embed the what/why/next feedback discipline."""
    prompt = grader_llm._build_prompt(
        question="Q",
        mark_scheme="MS",
        answer="A",
        max_marks=6,
        student_context=None,
    )
    lower = prompt.lower()
    # "what happened" must appear (discipline header)
    assert "what happened" in lower or "explain what" in lower, (
        "Prompt missing 'what happened' discipline marker"
    )
    # "why" must appear in the discipline section
    assert "why" in lower, "Prompt missing 'why' discipline marker"
    # "next step" or "actionable" must appear
    assert "next step" in lower or "actionable" in lower, (
        "Prompt missing 'next step' / 'actionable' discipline marker"
    )


def test_grader_prompt_discipline_present_without_student_context():
    """Discipline must appear even when no student context is provided."""
    prompt = grader_llm._build_prompt(
        question="Differentiate x^3",
        mark_scheme="M1 power rule; A1 correct",
        answer="3x^2",
        max_marks=2,
        student_context=None,
    )
    lower = prompt.lower()
    assert "what happened" in lower or "explain what" in lower
    assert "why" in lower
    assert "next step" in lower or "actionable" in lower


def test_grader_prompt_discipline_present_with_student_context():
    """Discipline markers must survive when student context is injected."""
    context = {
        "recent_grades": [
            {
                "grade_pct": 50,
                "marks_awarded": 3,
                "max_marks": 6,
                "improvement": "Show working",
                "days_ago": 5,
            }
        ],
        "mastery_trend": {"prev_mastery": 0.3, "current_mastery": 0.45, "trend": "up"},
        "recent_practice_mistakes": ["forgot +C"],
    }
    prompt = grader_llm._build_prompt(
        question="Integrate 2x",
        mark_scheme="M1 attempt; A1 correct; B1 +C",
        answer="x^2",
        max_marks=3,
        student_context=context,
    )
    lower = prompt.lower()
    assert "what happened" in lower or "explain what" in lower
    assert "why" in lower
    assert "next step" in lower or "actionable" in lower


# ── Memory / recency ordering tests (DB-backed) ───────────────────────────────

@pytest.mark.asyncio
async def test_grader_memory_prefers_most_recent(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    """recent_grades must be sorted so the most-recent attempt is index 0."""
    now = datetime.now(timezone.utc)

    # Add three graded uploads at different ages: 10 days, 5 days, 1 day ago
    for days_ago, grade_pct in [(10, 40.0), (5, 55.0), (1, 70.0)]:
        row = GradedUpload(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            exam_board="edexcel",
            question_id=f"q_recency_{days_ago}",
            question_text="Integrate 2x",
            mark_scheme="MS",
            max_marks=6,
            input_type="typed",
            answer_text="x^2 + C",
            marks_awarded=int(grade_pct / 100 * 6),
            grade_pct=grade_pct,
            feedback_json={"improvement": f"Tip from {days_ago}d ago"},
            status="graded",
        )
        # Manually set created_at by committing with a backdated value
        row.created_at = now - timedelta(days=days_ago)
        db_session.add(row)

    await db_session.flush()

    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics"
    )

    grades = ctx["recent_grades"]
    assert len(grades) >= 2, "Expected at least 2 grades in context"

    # Most-recent (1 day ago) must appear before oldest (10 days ago)
    assert grades[0]["days_ago"] <= grades[-1]["days_ago"], (
        f"Grades not sorted most-recent-first: {[g['days_ago'] for g in grades]}"
    )


@pytest.mark.asyncio
async def test_grader_memory_returns_empty_for_fresh_student(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    """A student with no submissions must have empty recent_grades."""
    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics"
    )
    assert ctx["recent_grades"] == []
