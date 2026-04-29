from typing import Any, Literal, TypedDict
import uuid


class Message(TypedDict):
    role: Literal["student", "tutor", "system"]
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
    current_input_type: Literal["text", "image"]
    image_bytes: bytes | None

    # Intent
    intent: Literal[
        "explain", "quiz", "hint",
        "check_answer", "off_topic", "greeting", "unknown"
    ]
    topic: str | None
    subtopic: str | None

    # RAG
    retrieved_chunks: list[dict[str, Any]]
    retrieval_query: str | None

    # Agent outputs
    explanation: str | None
    quiz_question: dict[str, Any] | None
    student_answer: str | None
    evaluation_result: dict[str, Any] | None
    hints_given: int

    # Rules engine
    rules_action: Literal[
        "continue", "re_explain", "switch_topic",
        "redirect_off_topic", "show_worked_example", "end_session"
    ]

    # Progress
    weak_topics: list[str]
    mastery_scores: dict[str, float]
    consecutive_wrong: int
    consecutive_correct: int

    # Session meta
    mode: Literal["explain", "quiz", "review", "exam_practice"]
    turn_count: int
    safety_flags: list[str]
    final_response: str | None
    error: str | None


def initial_state(
    student_id: str,
    subject: str,
    exam_board: str = "cambridge",
    exam_level: str = "a_level",
    subscription_tier: str = "free",
    mode: str = "explain",
) -> SessionState:
    return SessionState(
        session_id=str(uuid.uuid4()),
        student_id=student_id,
        subject=subject,
        exam_board=exam_board,
        exam_level=exam_level,
        subscription_tier=subscription_tier,
        conversation_history=[],
        current_input="",
        current_input_type="text",
        image_bytes=None,
        intent="unknown",
        topic=None,
        subtopic=None,
        retrieved_chunks=[],
        retrieval_query=None,
        explanation=None,
        quiz_question=None,
        student_answer=None,
        evaluation_result=None,
        hints_given=0,
        rules_action="continue",
        weak_topics=[],
        mastery_scores={},
        consecutive_wrong=0,
        consecutive_correct=0,
        mode=mode,
        turn_count=0,
        safety_flags=[],
        final_response=None,
        error=None,
    )