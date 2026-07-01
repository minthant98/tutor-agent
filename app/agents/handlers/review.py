from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer
from sqlalchemy.ext.asyncio import AsyncSession


async def _reframe_question(state: SessionState, topic: str, source: dict) -> dict:
    """Ask LLM for a variant of the original question testing the same concept."""
    return await generate_question(
        state,
        topic=topic,
        difficulty="medium",
        reframe_of={"question": source["question"], "mark_scheme": source["mark_scheme"]},
    )


async def _evaluate(state, question: str, mark_scheme: str, answer: str) -> dict:
    return await evaluate_answer(
        state,
        question=question,
        mark_scheme=mark_scheme,
        student_answer=answer,
    )


class ReviewHandler:
    name = "review"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})

        if "current_question" not in cfg:
            source = cfg.get("source")
            if not source:
                # Fall back to fresh question if no source provided
                q = await generate_question(
                    state,
                    topic=seg["topic"],
                    difficulty="medium",
                )
            else:
                q = await _reframe_question(state, seg["topic"], source)
            cfg["current_question"] = q
            return {
                "tutor_message": "Let's revisit this — same concept, slightly different framing.",
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        cur = cfg["current_question"]
        result = await _evaluate(state, cur["question"], cur["mark_scheme"], user_input)
        correct = bool(result.get("correct"))
        return {
            "tutor_message": result.get("feedback", ""),
            "structured_cards": [{"type": "evaluation", "data": result}],
            "segment_complete": True,
            "mastery_updates": [{
                "topic": seg["topic"],
                "mastery_score_delta": 0.15 if correct else 0.0,
                "attempt_delta": 1,
                "correct_delta": 1 if correct else 0,
            }],
        }

    async def initial_message(self, state: SessionState) -> str | None:
        return None


register_handler(ReviewHandler())
