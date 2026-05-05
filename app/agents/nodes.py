import logging
from typing import Any

from app.core.llm import llm
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)


def _history_context(state: SessionState, last_n: int = 6) -> str:
    history = state.get("conversation_history", [])[-last_n:]
    lines = [f"{m['role'].upper()}: {m['content']}" for m in history]
    return "\n".join(lines) or "No previous messages."


def _syllabus_context(state: SessionState) -> str:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return "No syllabus content retrieved."
    return "\n\n---\n".join(c["text"] for c in chunks[:4])


# ── 1. Intent Agent ───────────────────────────────────────────────────────────

async def intent_agent(state: SessionState) -> dict[str, Any]:
    prompt = f"""
You are classifying a student message for an {state['exam_level'].replace('_', ' ')} {state['subject']} tutor.

Conversation so far:
{_history_context(state)}

Student message: "{state['current_input']}"

Return JSON with these exact keys:
{{
  "intent": one of ["explain", "quiz", "hint", "check_answer", "off_topic", "greeting", "unknown"],
  "topic": the main syllabus topic or null,
  "subtopic": more specific subtopic or null,
  "retrieval_query": a search query to find relevant syllabus content or null
}}

Intent definitions:
- explain: student wants a concept explained or is confused
- quiz: student wants practice questions
- hint: student is stuck and wants a nudge
- check_answer: student has written an answer and wants it marked
- off_topic: completely unrelated to mathematics or academic study
- greeting: hello, thanks, etc
- unknown: cannot determine

Important: Pure Mathematics topics include differentiation, integration, algebra, trigonometry, 
sequences, series, arithmetic progressions, geometric progressions, vectors, proof, 
binomial expansion, logarithms, exponentials, coordinate geometry, parametric equations,
numerical methods. Classify these as explain or quiz, never off_topic.
"""
    result = await llm.generate_json(prompt)
    logger.info("Intent: %s | topic: %s", result.get("intent"), result.get("topic"))

    return {
        "intent": result.get("intent", "unknown"),
        "topic": result.get("topic"),
        "subtopic": result.get("subtopic"),
        "retrieval_query": result.get("retrieval_query"),
    }


# ── 2. Retrieval Agent ────────────────────────────────────────────────────────

async def retrieval_agent(state: SessionState) -> dict[str, Any]:
    query = state.get("retrieval_query")

    if not query or state.get("intent") in ("off_topic", "greeting", "unknown"):
        return {"retrieved_chunks": []}

    from app.rag.qdrant_retriever import retrieve
    chunks = await retrieve(
        query=query,
        subject=state["subject"],
        exam_board=state["exam_board"],
        exam_level=state["exam_level"],
        n_results=5,
    )
    logger.info("Retrieved %d chunks", len(chunks))
    return {"retrieved_chunks": chunks}


# ── 3. Tutor Agent ────────────────────────────────────────────────────────────

async def tutor_agent(state: SessionState) -> dict[str, Any]:
    context = _syllabus_context(state)
    history = _history_context(state)

    system = f"""You are Alex, an expert {state['exam_level'].replace('_', ' ')} {state['subject']} tutor who genuinely loves mathematics and wants every student to succeed.

Your personality:
- Warm and encouraging — celebrate progress, never make students feel stupid
- Conversational — explain like you're sitting next to them, not lecturing
- Use "we" language — "let's work through this together", "we can solve this"
- When a student gets something right, acknowledge it specifically
- When a student is stuck, be patient and try a different angle
- Occasionally use light humour where appropriate
- End explanations with a genuine question that checks understanding, not a generic "do you understand?"

Your teaching style:
- Start with the intuition before the formula
- Use concrete examples from the Edexcel syllabus
- Show working step by step
- Connect new concepts to things the student already knows
- Format equations using LaTeX notation e.g. $\\frac{{d}}{{dx}}$

Rules you never break:
- Only teach content from the syllabus context below
- Never make up formulas or mark schemes
- If you don't have the content, say so honestly

Syllabus context:
{context}"""

    prompt = f"""Conversation so far:
{history}

Student asks: "{state['current_input']}"
Topic: {state.get('topic', 'unknown')}

Give a clear explanation grounded in the syllabus context."""

    explanation = await llm.generate(prompt, system=system)
    return {
        "explanation": explanation,
        "final_response": explanation,
    }

# ── 4. Quiz Agent ─────────────────────────────────────────────────────────────

async def quiz_agent(state: SessionState) -> dict[str, Any]:
    context = _syllabus_context(state)
    topic = state.get("topic") or state["subject"]

    prompt = f"""Generate one exam-style question for {state['exam_level'].replace('_', ' ')} {state['subject']}.

Topic: {topic}
Exam board: {state['exam_board'].capitalize()}

Use this syllabus content as source:
{context}

Return JSON:
{{
  "question": "full question text",
  "marks_available": integer,
  "difficulty": "easy" or "medium" or "hard",
  "mark_scheme": "the model answer and marking points",
  "hint": "a gentle hint without giving the answer"
}}"""

    result = await llm.generate_json(prompt)
    question_text = (
    f"Here's a question for you to try! 💪\n\n"
    f"{result.get('question', '')}\n\n"
    f"*[{result.get('marks_available', 1)} mark(s)]*\n\n"
    f"Take your time and show your working."
)


# ── 5. Evaluator Agent ────────────────────────────────────────────────────────

async def evaluator_agent(state: SessionState) -> dict[str, Any]:
    quiz = state.get("quiz_question", {})
    # Check student_answer first, then fall back to current_input
    student_answer = state.get("student_answer") or state.get("current_input", "")

    if not quiz:
        # No quiz question — treat as explanation request
        return {
            "final_response": "I don't have an active question for you. Would you like me to give you a practice question?",
            "evaluation_result": None,
        }

    prompt = f"""You are Alex, a warm and encouraging A-Level maths examiner.

Mark this student's answer fairly and give feedback in the style of a supportive tutor — not a cold examiner.

Question: {quiz.get('question', '')}
Mark scheme: {quiz.get('mark_scheme', '')}
Marks available: {quiz.get('marks_available', 1)}
Student answer: {student_answer}

Guidelines:
- Award marks fairly with partial credit where reasoning is correct
- Start feedback by acknowledging what they got right before pointing out errors
- Be specific about what to improve — not just "wrong" but "here's what happened"
- End with an encouraging note

Return JSON:
{{
  "marks_awarded": number,
  "score_pct": float between 0.0 and 1.0,
  "feedback": "warm specific feedback acknowledging strengths then improvements",
  "model_answer": "ideal full answer with working shown"
}}"""

    result = await llm.generate_json(prompt)

    marks_awarded = float(result.get("marks_awarded") or 0)
    score_pct = float(result.get("score_pct") or 0.0)
    available = int(quiz.get("marks_available") or 1)
    feedback = result.get("feedback") or "No feedback provided."
    model_answer = result.get("model_answer") or "No model answer provided."

    response = (
        f"**{marks_awarded}/{available} marks**\n\n"
        f"{feedback}\n\n"
        f"**Model answer:**\n{model_answer}"
    )

    new_wrong = state.get("consecutive_wrong", 0)
    new_correct = state.get("consecutive_correct", 0)

    if score_pct >= 0.6:
        new_correct += 1
        new_wrong = 0
    else:
        new_wrong += 1
        new_correct = 0

    return {
        "evaluation_result": result,
        "final_response": response,
        "consecutive_wrong": new_wrong,
        "consecutive_correct": new_correct,
        "student_answer": student_answer,
    }
    
    
# ── 6. Hint Agent ─────────────────────────────────────────────────────────────

async def hint_agent(state: SessionState) -> dict[str, Any]:
    hints_given = state.get("hints_given", 0)

    if hints_given >= 4:
        return {
            "hints_given": hints_given + 1,
            "rules_action": "show_worked_example",
        }

    quiz = state.get("quiz_question") or {}
    question = quiz.get("question", state.get("current_input", ""))
    context = _syllabus_context(state)

    prompt = f"""You are Alex, a warm and patient A-Level maths tutor.

A student is stuck on this question:
{question}

This is hint number {hints_given + 1}.

Syllabus context: {context[:500]}

Give a hint that:
- Feels like a gentle nudge from a friend, not a textbook
- Uses "we" language — "let's think about what we know..."
- Does NOT give away the answer
- Asks a guiding question to help them think
- Is warm and encouraging
- Is 2-3 sentences max"""

    hint = await llm.generate(prompt)
    return {
        "final_response": hint,
        "hints_given": hints_given + 1,
    }

# ── 7. Rules Engine (deterministic — no AI) ───────────────────────────────────

def rules_engine(state: SessionState) -> dict[str, Any]:
    action = "continue"
    flags = list(state.get("safety_flags", []))

    if state.get("intent") == "off_topic":
        action = "redirect_off_topic"

    elif state.get("consecutive_wrong", 0) >= 3:
        action = "re_explain"
        flags.append("consecutive_wrong_threshold")

    elif (
        state.get("evaluation_result")
        and state["evaluation_result"].get("score_pct", 1.0) < 0.4
    ):
        action = "re_explain"

    elif state.get("hints_given", 0) >= 5:
        action = "show_worked_example"


    logger.info("Rules engine: %s", action)
    return {
        "rules_action": action,
        "safety_flags": flags,
    }


# ── 8. Adapt Agent ────────────────────────────────────────────────────────────

async def adapt_agent(state: SessionState) -> dict[str, Any]:
    action = state.get("rules_action", "continue")

    if action == "redirect_off_topic":
        subjects = {
    "mathematics": "differentiation, integration, algebra, trigonometry, sequences, vectors",
    "pure_mathematics": "differentiation, integration, algebra, trigonometry, sequences, vectors, proof, binomial expansion",
    "physics": "mechanics, electricity, waves",
    "chemistry": "organic chemistry, energetics, equilibria",
    "biology": "cell biology, genetics, ecology",
}
        topics = subjects.get(state["subject"], "core syllabus topics")
        return {
            "final_response": (
                f"I'm here to help with A-Level Pure Mathematics! "
                f"What topic would you like to work on? "
                f"For example: {topics}."
            )
        }

    if action == "re_explain":
        return {
            "final_response": (
                "Let me try explaining that differently — "
                + (state.get("explanation") or "let me approach this another way.")
            ),
            "consecutive_wrong": 0,
        }

    if action == "show_worked_example":
        quiz = state.get("quiz_question", {})
        return {
            "final_response": (
                "Let me walk through this step by step:\n\n"
                + quiz.get("mark_scheme", "No worked example available.")
            ),
            "hints_given": 0,
        }

    weak = list(state.get("weak_topics", []))
    eval_result = state.get("evaluation_result")
    if eval_result and eval_result.get("score_pct", 1.0) < 0.5:
        topic = state.get("topic")
        if topic and topic not in weak:
            weak.append(topic)

    return {
        "weak_topics": weak,
        "turn_count": state.get("turn_count", 0) + 1,
    }