from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from sqlalchemy.ext.asyncio import AsyncSession


class MistakesHandler:
    name = "mistakes"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})
        mistakes = cfg.get("mistakes", [])
        idx = cfg.get("idx", 0)

        if idx >= len(mistakes):
            return {
                "tutor_message": "Nice work — that's all the recent mistakes locked in.",
                "structured_cards": [],
                "segment_complete": True,
            }

        m = mistakes[idx]
        cfg["idx"] = idx + 1
        # Walk the student through the correct approach in narrative form
        msg = (
            f"Let's revisit: **{m['question']}**\n\n"
            f"Earlier you answered:\n\n> {m['student_answer']}\n\n"
            f"The mark scheme expected:\n\n> {m['mark_scheme']}\n\n"
            f"Let's walk through why."
        )
        return {
            "tutor_message": msg,
            "structured_cards": [{"type": "mistake_review", "data": m}],
            "segment_complete": False,
        }

    async def initial_message(self, state: SessionState) -> str | None:
        return None


register_handler(MistakesHandler())
