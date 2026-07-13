"""Alex session-scoped chat service.

Builds context from the live TutorSession and streams a response from the LLM.
Context is derived from segment_plan[current_segment_idx] and the session's
top-level fields — no dedicated `state` column exists on TutorSession.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import TutorSession
from app.core.llm import llm

logger = logging.getLogger(__name__)

# ── Hard behavioural constraints ─────────────────────────────────────────────

SYSTEM_INSTRUCTION = """You are Alex, a concise analytical tutor helping a student mid-session.

HARD RULES:
- NEVER invent facts about the student's history not provided below
- Analytical, never motivational — no "great job", "well done", "you've got this"
- Reference the current question/segment specifically; the student is looking at it right now
- Keep responses concise: 1–4 sentences typical

You will receive structured context about the student's current position in the session.
Stick to what is known. If context is sparse, answer only what you can from the question itself."""


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _load_session(db: AsyncSession, session_id: str) -> TutorSession | None:
    result = await db.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )
    return result.scalar_one_or_none()


# ── Context builder ───────────────────────────────────────────────────────────

async def build_context(
    db: AsyncSession,
    student_id: str,
    session_id: str,
) -> dict:
    """Return a dict describing the student's current session state.

    Fields:
      - topic: str | None
      - current_segment_intent: str | None  (e.g. "teach", "reinforce", "assess")
      - current_question: str | None        (from segment config["current_question"])
      - submitted_work: str | None          (from segment config["submitted_work"])
      - recent_mistakes: list[str]          (from segment config["mistakes"] or [])
    """
    session = await _load_session(db, session_id)
    if session is None:
        return {
            "topic": None,
            "current_segment_intent": None,
            "current_question": None,
            "submitted_work": None,
            "recent_mistakes": [],
        }

    # Ownership is checked at the endpoint layer; here we just build context.
    plan: list = session.segment_plan or []
    idx: int = session.current_segment_idx or 0

    current_segment: dict = plan[idx] if plan and 0 <= idx < len(plan) else {}
    cfg: dict = current_segment.get("config", {}) if current_segment else {}

    # current_question may be a dict (Qdrant doc) or a plain string
    raw_q = cfg.get("current_question")
    if isinstance(raw_q, dict):
        current_question = raw_q.get("question_text") or raw_q.get("text") or str(raw_q)
    else:
        current_question = raw_q  # str or None

    return {
        "topic": session.topic,
        "current_segment_intent": current_segment.get("intent"),
        "current_question": current_question,
        "submitted_work": cfg.get("submitted_work"),
        "recent_mistakes": cfg.get("mistakes", cfg.get("session_mistakes", [])),
    }


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(context: dict, user_message: str) -> str:
    """Build the user-turn prompt that injects session context."""
    lines = ["=== SESSION CONTEXT ==="]

    if context.get("topic"):
        lines.append(f"Topic: {context['topic']}")
    if context.get("current_segment_intent"):
        lines.append(f"Segment type: {context['current_segment_intent']}")
    if context.get("current_question"):
        lines.append(f"Current question: {context['current_question']}")
    if context.get("submitted_work"):
        lines.append(f"Student's submitted work: {context['submitted_work']}")
    mistakes = context.get("recent_mistakes") or []
    if mistakes:
        lines.append(f"Recent mistakes in this session: {'; '.join(str(m) for m in mistakes)}")

    lines.append("")
    lines.append("RULE: Do not invent any facts not listed above.")
    lines.append("")
    lines.append(f"Student asks: {user_message}")

    return "\n".join(lines)


# ── Streaming entry point ─────────────────────────────────────────────────────

async def stream_alex_reply(
    db: AsyncSession,
    student_id: str,
    session_id: str,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """Stream Alex's response tokens for a given session context."""
    context = await build_context(db, student_id, session_id)
    prompt = build_prompt(context, user_message)

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    async for token in llm.stream(messages):
        yield token
