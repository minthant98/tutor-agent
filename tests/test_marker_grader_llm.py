import json
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.services.marker import grader_llm
from app.db.models import MasteryState, GradedUpload


VALID_LLM_JSON = json.dumps({
    "marks_awarded": 4,
    "criteria": [
        {"code": "M1", "description": "Applied chain rule",
         "awarded": True, "comment": "Correctly identified inner and outer"},
        {"code": "A1", "description": "Correct derivative",
         "awarded": True, "comment": ""},
        {"code": "M1", "description": "Substituted correctly",
         "awarded": False, "comment": "Used x=2 instead of x=3"},
        {"code": "B1", "description": "Final numerical answer stated",
         "awarded": False, "comment": "No final answer given"},
    ],
    "summary": "Solid method setup but arithmetic slip.",
    "improvement": "Always box or underline your final numerical answer.",
})


@pytest.mark.asyncio
async def test_grade_returns_structured_result():
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=VALID_LLM_JSON)):
        result = await grader_llm.grade(
            question="Find dy/dx of (x^2+1)^3",
            mark_scheme="M1 chain rule, A1 correct, B1 final",
            answer="3(x^2+1)^2 * 2x",
            max_marks=6,
        )
    assert result["marks_awarded"] == 4
    assert len(result["criteria"]) == 4
    assert result["improvement"].endswith("numerical answer.")


@pytest.mark.asyncio
async def test_grade_clamps_over_max():
    over_max_json = json.dumps({
        "marks_awarded": 10,  # over max
        "criteria": [], "summary": "s", "improvement": "i",
    })
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=over_max_json)):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert result["marks_awarded"] == 6


@pytest.mark.asyncio
async def test_grade_clamps_below_zero():
    neg_json = json.dumps({
        "marks_awarded": -1,
        "criteria": [], "summary": "s", "improvement": "i",
    })
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=neg_json)):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert result["marks_awarded"] == 0


@pytest.mark.asyncio
async def test_grade_retries_on_invalid_json():
    """First LLM call returns garbage, second returns valid JSON."""
    call_count = {"n": 0}

    async def sometimes_valid(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return "not json"
        return VALID_LLM_JSON

    with patch.object(grader_llm, "_call_llm", side_effect=sometimes_valid):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert call_count["n"] == 2
    assert result["marks_awarded"] == 4


@pytest.mark.asyncio
async def test_grade_raises_after_two_bad_responses():
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value="not json")):
        with pytest.raises(grader_llm.GradingFailed):
            await grader_llm.grade(question="Q", mark_scheme="MS", answer="A", max_marks=6)


@pytest.mark.asyncio
async def test_grade_includes_student_context_in_prompt():
    """When student_context is passed, the prompt should include it."""
    captured_prompt = {}

    async def capture(prompt):
        captured_prompt["text"] = prompt
        return VALID_LLM_JSON

    context = {
        "recent_grades": [
            {"grade_pct": 33, "marks_awarded": 2, "max_marks": 6,
             "improvement": "Show working", "days_ago": 4},
        ],
        "mastery_trend": {"prev_mastery": 0.20, "current_mastery": 0.35, "trend": "up"},
        "recent_practice_mistakes": ["forgot +C"],
    }
    with patch.object(grader_llm, "_call_llm", side_effect=capture):
        await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
            student_context=context,
        )
    assert "student_history" in captured_prompt["text"]
    assert "33%" in captured_prompt["text"]
    assert "forgot +C" in captured_prompt["text"]


@pytest.mark.asyncio
async def test_load_student_topic_context_empty_for_fresh_student(db_session, student_with_subject):
    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics"
    )
    assert ctx["recent_grades"] == []
    assert ctx["recent_practice_mistakes"] == []
    assert ctx["mastery_trend"]["current_mastery"] == 0.0


@pytest.mark.asyncio
async def test_load_student_topic_context_returns_recent_grades(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    db_session.add(GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q1", question_text="Old",
        mark_scheme="MS", max_marks=6, input_type="typed", answer_text="A",
        marks_awarded=2, grade_pct=33.3,
        feedback_json={"improvement": "Show working"},
        status="graded",
    ))
    db_session.add(MasteryState(
        student_id=student_with_subject.id, subject="pure_mathematics",
        topic="integration_basics", mastery_score=0.35, total_attempts=3,
        last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    await db_session.flush()

    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics",
    )
    assert len(ctx["recent_grades"]) == 1
    assert ctx["recent_grades"][0]["grade_pct"] == pytest.approx(33.3, abs=0.5)
    assert ctx["mastery_trend"]["current_mastery"] == pytest.approx(0.35)


@pytest.mark.asyncio
async def test_load_context_handles_tz_aware_datetime_from_committed_row(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    """Regression: don't call .replace(tzinfo=...) on a tz-aware datetime."""
    db_session.add(GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q_tz", question_text="Q",
        mark_scheme="MS", max_marks=6, input_type="typed", answer_text="A",
        marks_awarded=3, grade_pct=50.0,
        feedback_json={"improvement": ""},
        status="graded",
    ))
    await db_session.commit()  # forces server_default to fire → tz-aware created_at

    # Should not raise
    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics",
    )
    assert len(ctx["recent_grades"]) >= 1
