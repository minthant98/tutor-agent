import json
import logging
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_syllabus",
            "description": (
                "Search Edexcel syllabus content, past papers, and mark schemes for relevant material. "
                "Always call this before explaining any concept or topic to the student."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for, e.g. 'integration by parts formula and method'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_question",
            "description": (
                "Generate a practice question with mark scheme for the student to attempt. "
                "Call when moving to the warm-up or main phase, or when the student asks for practice."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Specific topic, e.g. 'integration by parts'"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"]
                    }
                },
                "required": ["topic", "difficulty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_answer",
            "description": (
                "Evaluate a student's submitted answer against a mark scheme. "
                "Call when the student shows their working or states a final answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The original question text"
                    },
                    "mark_scheme": {
                        "type": "string",
                        "description": "The mark scheme from generate_question"
                    },
                    "student_answer": {
                        "type": "string",
                        "description": "The student's full response or working"
                    }
                },
                "required": ["question", "mark_scheme", "student_answer"]
            }
        }
    }
]


async def execute_tool(name: str, args: dict, state: SessionState) -> str:
    if name == "search_syllabus":
        return await _search_syllabus(args, state)
    if name == "generate_question":
        return await _generate_question(args, state)
    if name == "evaluate_answer":
        return await _evaluate_answer(args, state)
    logger.warning("Unknown tool called: %s", name)
    return "Tool not found."


async def _search_syllabus(args: dict, state: SessionState) -> str:
    from app.rag.qdrant_retriever import retrieve
    chunks = await retrieve(
        query=args["query"],
        subject=state["subject"],
        exam_board=state["exam_board"],
        exam_level=state["exam_level"],
        n_results=4,
    )
    if not chunks:
        return "No relevant syllabus content found."
    return "\n\n---\n".join(c["text"] for c in chunks)


async def _generate_question(args: dict, state: SessionState) -> str:
    from app.core.llm import llm
    subject = state["subject"].replace("_", " ")
    exam_board = state["exam_board"].upper()

    prompt = f"""Generate one {args['difficulty']} exam-style question for {exam_board} A-Level {subject}.
Topic: {args['topic']}

Return JSON only — no markdown fences, no extra text:
{{"question": "full question text with any needed context or values", "marks_available": integer, "mark_scheme": "full model answer with all marking points", "difficulty": "{args['difficulty']}"}}"""

    result = await llm.generate_json(prompt)
    return json.dumps(result)


async def _evaluate_answer(args: dict, state: SessionState) -> str:
    from app.core.llm import llm
    from app.core.math_validator import validate_answer

    sympy_result = validate_answer(args["student_answer"], args["mark_scheme"])
    sympy_note = ""
    if sympy_result["method"] == "sympy":
        if sympy_result["is_correct"]:
            sympy_note = "SymPy confirms: student answer is mathematically equivalent to the mark scheme."
        else:
            sympy_note = f"SymPy detected an error: {sympy_result['reason']}"

    subject = state["subject"].replace("_", " ")
    prompt = f"""Evaluate this A-Level {subject} answer.

Question: {args['question']}
Mark scheme: {args['mark_scheme']}
Student answer: {args['student_answer']}
{sympy_note}

Return JSON only — no markdown fences:
{{"marks_awarded": integer, "marks_available": integer, "score_pct": float, "topic": "specific topic name e.g. integration by parts", "correct_steps": ["what the student got right"], "errors": ["specific errors, or empty list if full marks"]}}"""

    result = await llm.generate_json(prompt)

    # Update weak topics in state and flag for DB mastery sync after this turn
    topic = result.get("topic")
    score = float(result.get("score_pct") or 0.0)
    if topic:
        state["pending_mastery"] = {"topic": topic, "score": score}
        weak = list(state.get("weak_topics", []))
        if score < 0.5 and topic not in weak:
            weak.append(topic)
        elif score >= 0.8 and topic in weak:
            weak.remove(topic)
        state["weak_topics"] = weak

    return json.dumps(result)
