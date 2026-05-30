import json
import logging
from datetime import date
from typing import AsyncGenerator, Literal

from app.agents.tools import TOOL_SCHEMAS, execute_tool
from app.core.llm import llm, LLMError
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

Signal = Literal["explain", "guide"] | None

_PHASE_INSTRUCTIONS: dict[str, str] = {
    "diagnostic": (
        "Ask ONE open question to find out what the student already knows. "
        "Do not call generate_question yet."
    ),
    "warmup": (
        "Call generate_question with difficulty='easy' to give the student a confidence-building question. "
        "Be warm and encouraging."
    ),
    "main": (
        "Work through questions at the right difficulty. "
        "Be Socratic — ask a leading question before giving a hint. "
        "Call generate_question when the student is ready for the next question."
    ),
    "consolidation": (
        "Summarise what was covered. Name specifically what clicked and what still needs work. "
        "End with one clear focus for next time."
    ),
}


def _days_to_exam(state: SessionState) -> str:
    exam_date_str = state.get("exam_date")
    if not exam_date_str:
        return "date not set"
    try:
        delta = (date.fromisoformat(exam_date_str) - date.today()).days
        if delta > 0:
            return f"{delta} days"
        return "exam has passed"
    except ValueError:
        return "date not set"


def _build_system_prompt(state: SessionState, signal: Signal) -> str:
    weak = state.get("weak_topics", [])
    summaries = state.get("session_summaries", [])
    phase = state.get("session_phase", "diagnostic")
    goal = state.get("session_goal") or "identify what the student knows and where to start"
    exam_board = state["exam_board"].upper()
    subject = state["subject"].replace("_", " ").title()

    past_context = ""
    if summaries:
        past_context = "\nPrevious sessions:\n" + "\n".join(f"- {s}" for s in summaries[-2:])

    signal_override = ""
    if signal == "explain":
        signal_override = (
            "\n\nSTUDENT CLICKED 'EXPLAIN THIS CONCEPT': "
            "Call search_syllabus now, then explain the concept clearly and show ONE similar worked example. "
            "Do NOT solve the student's exact question for them. "
            "After explaining, ask them to try their question with this new understanding."
        )
    elif signal == "guide":
        signal_override = (
            "\n\nSTUDENT CLICKED 'GUIDE ME': "
            "Give one scaffolded hint only. "
            "Ask one leading question after the hint. "
            "Wait for their response before giving another hint."
        )

    return f"""You are Alex, a Socratic {exam_board} A-Level {subject} tutor.

CORE RULE: Never give the direct answer to the student's specific question. Guide them to find it themselves.

WHEN TO EXPLAIN DIRECTLY (exceptions to the core rule):
- Student explicitly requests explanation via the 'Explain this concept' button (signal below will say so)
- Student makes 3 or more failed attempts at the same step
In these cases: explain the concept and show a SIMILAR worked example — not the student's exact question.

Student:
- Exam in {_days_to_exam(state)}
- Weak topics: {', '.join(weak) if weak else 'not yet identified'}
- Session goal: {goal}{past_context}

Current phase: {phase}
{_PHASE_INSTRUCTIONS.get(phase, '')}
{signal_override}

Conversation style:
- Warm and encouraging — use "we" and "let's work through this together"
- Ask ONE question at a time, never stack multiple questions
- When the student gets something right, name specifically what they did well
- Use LaTeX for all mathematical expressions: $x^2$, $\\frac{{dy}}{{dx}}$, $\\int_0^1 x\\,dx$

Tools:
- search_syllabus: call this before explaining any concept
- generate_question: call for warm-up and main phase practice questions
- evaluate_answer: call when the student submits an answer or shows their working"""


def _build_messages(state: SessionState, signal: Signal) -> list[dict]:
    messages: list[dict] = [
        {"role": "system", "content": _build_system_prompt(state, signal)}
    ]
    for msg in state.get("conversation_history", []):
        role = "user" if msg["role"] == "student" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": state["current_input"]})
    return messages


async def generate_opening_message(state: SessionState) -> str:
    """
    Generate a personalized first message from Alex when a session starts.
    New students get a diagnostic question. Returning students get a warm reference
    to their previous weak areas.
    """
    exam_board = state["exam_board"].upper()
    subject = state["subject"].replace("_", " ").title()
    days = _days_to_exam(state)
    weak = state.get("weak_topics", [])
    summaries = state.get("session_summaries", [])
    is_returning = bool(weak or summaries)

    if is_returning:
        weak_str = ", ".join(weak[:3]) if weak else "various topics"
        last_summary = f"\nLast session: {summaries[-1]}" if summaries else ""
        prompt = f"""You are Alex, a warm {exam_board} A-Level {subject} tutor.

This student is returning. Their weak areas: {weak_str}.{last_summary}

Write a natural 2-3 sentence opening message that:
- Welcomes them back warmly (no "Hi" or "Hello" — be more natural)
- References their specific weak area
- Asks if they want to continue with that or work on something else
- Feels like a real person, not a chatbot

Write only the message. No quotes."""
    else:
        prompt = f"""You are Alex, a warm {exam_board} A-Level {subject} tutor meeting a student for the first time.

Their exam is in {days}.

Write a natural 2-3 sentence opening message that:
- Acknowledges the exam timeline with encouraging urgency (mention {days} specifically)
- Says you want to see where they're starting from
- Ends with ONE open diagnostic question about {subject} to calibrate their level
  (e.g. "tell me in your own words what differentiation does" — conceptual, not a calculation)
- Feels conversational and warm, like sitting next to them

Write only the message. No quotes."""

    try:
        return await llm.generate(prompt)
    except LLMError:
        subject_display = state["subject"].replace("_", " ")
        return (
            f"Great to meet you! You've got {days} until your {subject_display} exam — "
            f"let's make the most of it. To start, tell me in your own words: "
            f"what's one topic in {subject_display} you feel least confident about right now?"
        )


async def run_agent(
    state: SessionState,
    signal: Signal = None,
) -> AsyncGenerator[str, None]:
    """
    Single agent turn. Yields streaming response tokens.
    May mutate state.weak_topics and state.pending_mastery via tool side-effects.
    """
    messages = _build_messages(state, signal)

    # Phase 1: tool selection — non-streaming, fast (~200ms)
    try:
        assistant_msg = await llm.chat_with_tools(messages, TOOL_SCHEMAS)
    except LLMError as e:
        logger.error("Tool selection failed: %s", e)
        yield "I ran into a problem — please try again."
        return

    tool_calls = assistant_msg.get("tool_calls") or []

    if tool_calls:
        messages.append(assistant_msg)
        for call in tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            logger.info("Tool: %s | args: %s", name, list(args.keys()))
            result = await execute_tool(name, args, state)
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": call["id"],
            })

    # Phase 2: stream final response
    try:
        async for token in llm.stream(messages):
            yield token
    except LLMError as e:
        logger.error("Streaming failed: %s", e)
        yield "\n\nSomething went wrong. Please try again."
