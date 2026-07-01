from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer

MAX_QUESTIONS = 3


async def _generate_question(state: SessionState, topic: str, with_hints: bool) -> dict:
    return await generate_question(
        state,
        topic=topic,
        difficulty="medium",
        with_hints=with_hints,
    )


async def _evaluate(state, question: str, mark_scheme: str, answer: str) -> dict:
    return await evaluate_answer(state, question=question, mark_scheme=mark_scheme, student_answer=answer)


class PracticeHandler:
    name = "practice"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})
        allow_hints = cfg.get("allow_hints", True)

        # No current question → emit one
        if "current_question" not in cfg:
            q = await _generate_question(state, seg["topic"], with_hints=allow_hints)
            cfg["current_question"] = q
            cfg["questions_asked"] = cfg.get("questions_asked", 0) + 1
            return {
                "tutor_message": None,
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        # Student answered → evaluate
        cur = cfg["current_question"]
        eval_result = await _evaluate(state, cur["question"], cur["mark_scheme"], user_input)
        correct = bool(eval_result.get("correct"))

        # Mastery update for every attempt
        updates = [{
            "topic": seg["topic"],
            "mastery_score_delta": 0.1 if correct else -0.05,
            "attempt_delta": 1,
            "correct_delta": 1 if correct else 0,
        }]

        # Termination: correct OR max questions hit
        if correct or cfg["questions_asked"] >= MAX_QUESTIONS:
            return {
                "tutor_message": eval_result.get("feedback", ""),
                "structured_cards": [{"type": "evaluation", "data": eval_result}],
                "segment_complete": True,
                "mastery_updates": updates,
            }

        # Wrong but more questions allowed → emit next
        del cfg["current_question"]
        return {
            "tutor_message": eval_result.get("feedback", "") + " Let's try another.",
            "structured_cards": [{"type": "evaluation", "data": eval_result}],
            "segment_complete": False,
            "mastery_updates": updates,
        }

    async def initial_message(self, state):
        seg = state["segment_plan"][state["current_segment_idx"]]
        return f"Let's practise **{seg['topic'].replace('_', ' ')}**."


register_handler(PracticeHandler())
