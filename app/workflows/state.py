from typing import Any, Literal, TypedDict
import uuid


class Message(TypedDict):
    role: Literal["student", "tutor"]
    content: str
    metadata: dict[str, Any]


class SessionState(TypedDict):
    # Identity
    session_id: str
    student_id: str
    subject: str
    exam_board: str
    exam_level: str
    subscription_tier: str

    # Conversation
    conversation_history: list[Message]
    current_input: str

    # Session structure
    session_goal: str | None
    session_phase: Literal["diagnostic", "warmup", "main", "consolidation"]
    exam_date: str | None  # ISO format: "2026-06-15"

    # Progress (weak_topics persisted to DB; session_summaries injected at session start for Pro)
    weak_topics: list[str]
    mastery_scores: dict[str, float]
    session_summaries: list[str]

    # Set by evaluate_answer tool; cleared by session_service after DB sync
    pending_mastery: dict[str, Any] | None

    # Meta
    turn_count: int
    error: str | None


def initial_state(
    student_id: str,
    subject: str,
    exam_board: str = "edexcel",
    exam_level: str = "a_level",
    subscription_tier: str = "free",
    exam_date: str | None = None,
    weak_topics: list[str] | None = None,
    mastery_scores: dict[str, float] | None = None,
    session_summaries: list[str] | None = None,
) -> SessionState:
    return {  # type: ignore[return-value]
        "session_id": str(uuid.uuid4()),
        "student_id": student_id,
        "subject": subject,
        "exam_board": exam_board,
        "exam_level": exam_level,
        "subscription_tier": subscription_tier,
        "conversation_history": [],
        "current_input": "",
        "session_goal": None,
        "session_phase": "diagnostic",
        "exam_date": exam_date,
        "weak_topics": weak_topics or [],
        "mastery_scores": mastery_scores or {},
        "session_summaries": session_summaries or [],
        "pending_mastery": None,
        "turn_count": 0,
        "error": None,
    }
