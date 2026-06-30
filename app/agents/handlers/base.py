from typing import Any, Protocol, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from app.workflows.state import SessionState


class HandlerResult(TypedDict, total=False):
    tutor_message: str | None         # streamed text to send
    structured_cards: list[dict]       # question/eval cards
    segment_complete: bool             # if True, orchestrator advances
    mastery_updates: list[dict]        # [{topic, delta, attempt_count}]
    error: str | None


class SegmentHandler(Protocol):
    name: str

    async def step(
        self,
        state: SessionState,
        db: AsyncSession,
        redis,
        user_input: str,
    ) -> HandlerResult: ...

    async def initial_message(self, state: SessionState) -> str | None:
        """Optional opener for the segment (e.g., 'Let's start with integration.')."""
        return None


HANDLER_REGISTRY: dict[str, SegmentHandler] = {}


def register_handler(handler: SegmentHandler) -> None:
    HANDLER_REGISTRY[handler.name] = handler
