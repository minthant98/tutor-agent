from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer


async def _generate_question(state: SessionState, topic: str) -> dict:
    """Thin wrapper so tests can patch."""
    return await generate_question(
        state,
        topic=topic,
        difficulty="medium",
        with_hints=False,
    )


async def _evaluate(state: SessionState, question: str, mark_scheme: str, answer: str) -> dict:
    return await evaluate_answer(
        state,
        question=question,
        mark_scheme=mark_scheme,
        student_answer=answer,
    )


class DiagnosticHandler:
    name = "diagnostic_question"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})

        if not cfg.get("question_emitted"):
            q = await _generate_question(state, seg["topic"])
            cfg["question_emitted"] = True
            cfg["question"] = q.get("question", q.get("question", ""))
            cfg["mark_scheme"] = q.get("mark_scheme", "")
            return {
                "tutor_message": "Here's your calibration question — no hints, no second tries. Take your time.",
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        # Student has answered
        eval_result = await _evaluate(state, cfg["question"], cfg["mark_scheme"], user_input)
        correct = bool(eval_result.get("correct"))
        return {
            "tutor_message": eval_result.get("feedback", ""),
            "structured_cards": [{"type": "evaluation", "data": eval_result}],
            "segment_complete": True,
            "mastery_updates": [{
                "topic": seg["topic"],
                "mastery_score": 0.6 if correct else 0.2,
                "attempt_delta": 1,
                "correct_delta": 1 if correct else 0,
            }],
        }

    async def initial_message(self, state: SessionState) -> str | None:
        return None  # opener emitted as part of first step


register_handler(DiagnosticHandler())
