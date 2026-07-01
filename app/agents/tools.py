import asyncio
import json
import logging
from app.core.telemetry import capture
from app.workflows.state import SessionState

# ---------------------------------------------------------------------------
# Public async wrappers — called by segment handlers (Tasks 9–11)
# ---------------------------------------------------------------------------


async def generate_question(
    state: "SessionState",
    *,
    topic: str,
    difficulty: str = "medium",
    with_hints: bool = True,
    reframe_of: dict | None = None,
) -> dict:
    """Public wrapper around _generate_question for use in segment handlers.

    Note: _generate_question uses topic and difficulty from args;
    subject/exam_board/level come from state. reframe_of, if provided, is
    passed through so the LLM produces a variant of the original question
    rather than a fresh one.
    """
    args = {"topic": topic, "difficulty": difficulty}
    if reframe_of is not None:
        args["reframe_of"] = reframe_of  # type: ignore[assignment]
    raw = await _generate_question(args, state)
    result = json.loads(raw)
    # Normalise key so handlers can access question text as result["question"]
    return result


async def evaluate_answer(
    state: "SessionState",
    *,
    question: str,
    mark_scheme: str,
    student_answer: str,
) -> dict:
    """Public wrapper around _evaluate_answer for use in segment handlers.

    Adds a synthetic 'correct' boolean (score_pct >= 60) so handlers can
    branch without repeating the threshold check.
    """
    args = {"question": question, "mark_scheme": mark_scheme, "student_answer": student_answer}
    raw = await _evaluate_answer(args, state)
    result = json.loads(raw)
    # Add convenience field
    score_pct = float(result.get("score_pct") or 0.0)
    # score_pct may be 0–1 or 0–100 depending on LLM; _evaluate_answer normalises to 0–1 in state
    # but the JSON it returns may still be 0–100. Normalise here too.
    if score_pct > 1.0:
        score_pct = score_pct / 100.0
    result["correct"] = score_pct >= 0.6
    # Also add feedback convenience key if not present
    if "feedback" not in result:
        errors = result.get("errors") or []
        correct_steps = result.get("correct_steps") or []
        if result["correct"]:
            result["feedback"] = f"Well done! {' '.join(correct_steps[:1])}"
        else:
            result["feedback"] = f"Not quite. {' '.join(errors[:1])}"
    return result

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_syllabus",
            "description": (
                "Search syllabus content, past papers, and mark schemes for relevant material. "
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
    from app.rag.qdrant_retriever import retrieve

    subject = state["subject"].replace("_", " ")
    exam_board = state["exam_board"].upper()
    topic = args["topic"]
    difficulty = args["difficulty"]

    # Pull past paper questions and real mark schemes separately so the LLM
    # sees both — questions for style, mark schemes for marking format.
    question_examples, scheme_examples = await asyncio.gather(
        retrieve(
            query=f"{topic} exam question",
            subject=state["subject"],
            exam_board=state["exam_board"],
            exam_level=state["exam_level"],
            n_results=2,
            doc_types=["past_paper"],
        ),
        retrieve(
            query=f"{topic} mark scheme marking points",
            subject=state["subject"],
            exam_board=state["exam_board"],
            exam_level=state["exam_level"],
            n_results=2,
            doc_types=["mark_scheme"],
        ),
    )

    question_block = ""
    if question_examples:
        snippets = [f"--- Past paper example {i+1} ({e['metadata'].get('year','')}) ---\n{e['text'][:400]}"
                    for i, e in enumerate(question_examples)]
        question_block = "\n\nReal past paper questions for style reference:\n" + "\n\n".join(snippets)

    scheme_block = ""
    if scheme_examples:
        snippets = [f"--- Real mark scheme {i+1} ({e['metadata'].get('year','')}) ---\n{e['text'][:600]}"
                    for i, e in enumerate(scheme_examples)]
        scheme_block = "\n\nReal mark schemes for marking format reference:\n" + "\n\n".join(snippets)

    reframe_block = ""
    if reframe_of := args.get("reframe_of"):
        reframe_block = (
            f"\n\nReframe this original question in a slightly different way, "
            f"testing the same concept with different numbers or context:\n"
            f"Original question: {reframe_of['question']}\n"
            f"Original mark scheme: {reframe_of['mark_scheme']}\n"
        )

    prompt = f"""Generate one {difficulty} exam-style question for {exam_board} A-Level {subject}.
Topic: {topic}{question_block}{scheme_block}{reframe_block}

Rules for the question:
- Match the style, notation, and difficulty of the real past paper examples
- Do NOT copy a real question directly — create an original one inspired by the style
- Use realistic numerical values typical of {exam_board} papers

Rules for the mark scheme (MUST follow the format of the real mark schemes above):
- Use the same per-step structure: each marking point on its own line
- Use {exam_board}-standard mark codes — typically [M1] for method marks, [A1] for accuracy marks, [B1] for independent marks
- Show the expected working at each step, not just the final answer
- Total marks across all points must equal marks_available

Return JSON only — no markdown fences, no extra text:
{{"question": "full question text", "marks_available": integer, "mark_scheme": "full mark scheme matching real format above", "difficulty": "{difficulty}"}}"""

    result = await llm.generate_json(prompt)
    capture(state["student_id"], "question_generated", {
        "topic": topic,
        "difficulty": difficulty,
        "marks_available": result.get("marks_available", 0),
        "phase": state.get("session_phase"),
        "exam_board": state.get("exam_board"),
    })
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

    capture(state["student_id"], "answer_evaluated", {
        "topic": result.get("topic", ""),
        "marks_awarded": result.get("marks_awarded", 0),
        "marks_available": result.get("marks_available", 0),
        "score_pct": result.get("score_pct", 0),
        "error_count": len(result.get("errors", []) or []),
        "phase": state.get("session_phase"),
        "exam_board": state.get("exam_board"),
        "sympy_method": sympy_result.get("method"),
    })

    return json.dumps(result)
