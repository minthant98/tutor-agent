"""Regression tests: _generate_question and _evaluate_answer must NOT mutate
state["last_question"], state["last_evaluation"], or state["pending_mastery"].

Finding 1-A from Phase C code review.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.tools import generate_question, evaluate_answer
from app.workflows.state import initial_state


def _make_state():
    s = initial_state(student_id="stu-1", subject="pure_mathematics")
    s["exam_board"] = "edexcel"
    s["exam_level"] = "a_level"
    return s


@pytest.mark.asyncio
async def test_generate_question_does_not_mutate_last_question():
    state = _make_state()
    assert state["last_question"] is None

    fake_result = {
        "question": "Differentiate x^2.",
        "mark_scheme": "[M1] 2x [A1]",
        "marks_available": 2,
        "difficulty": "medium",
    }

    with patch("app.agents.tools._generate_question", new=AsyncMock(return_value=json.dumps(fake_result))):
        result = await generate_question(state, topic="differentiation", difficulty="medium")

    # state["last_question"] must remain untouched
    assert state["last_question"] is None, (
        "generate_question must NOT mutate state['last_question']"
    )
    # The wrapper should still return the result dict to the caller
    assert result["question"] == "Differentiate x^2."


@pytest.mark.asyncio
async def test_evaluate_answer_does_not_mutate_last_evaluation_or_pending_mastery():
    state = _make_state()
    assert state["last_evaluation"] is None
    assert state["pending_mastery"] is None

    fake_result = {
        "marks_awarded": 2,
        "marks_available": 2,
        "score_pct": 100.0,
        "topic": "differentiation",
        "correct_steps": ["2x is correct"],
        "errors": [],
    }

    with patch("app.agents.tools._evaluate_answer", new=AsyncMock(return_value=json.dumps(fake_result))):
        result = await evaluate_answer(
            state,
            question="Differentiate x^2.",
            mark_scheme="[M1] 2x [A1]",
            student_answer="2x",
        )

    # Neither state field must be mutated
    assert state["last_evaluation"] is None, (
        "evaluate_answer must NOT mutate state['last_evaluation']"
    )
    assert state["pending_mastery"] is None, (
        "evaluate_answer must NOT mutate state['pending_mastery']"
    )
    # Caller still gets the result
    assert result["correct"] is True
