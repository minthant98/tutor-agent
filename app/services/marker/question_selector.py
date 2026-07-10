"""Question selection + Qdrant retrieval + mark scheme pairing for Exam Marker.

Serves real Edexcel/Cambridge past-paper questions from Qdrant. Falls back to
LLM-generated mark schemes when Qdrant pairing metadata is absent.

IMPORTANT: Qdrant chunks do NOT have `paper_ref` or `question_number` fields.
The ingested payload schema is:
  {text, source_file, exam_board, subject, exam_level, doc_type, year}

Therefore _fetch_mark_scheme cannot reliably pair a mark scheme to a specific
question — it will return None in production and _generate_mark_scheme_llm is
what runs. `used_generated_mark_scheme` will always be True in production until
a richer ingestion pipeline is added. This is MVP-accepted.

When Qdrant returns zero candidates entirely (e.g. missing collection, 404, or
unindexed board/subject), pick_question falls back to LLM-generated question +
mark scheme. paper_ref becomes "Alex-generated practice question" so the UI
never falsely attributes generated content to a real past paper.
"""
import logging
import random
import re
from typing import TypedDict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm  # existing Groq client with fallback chain
from app.db.models import GradedUpload
from app.services.planners.base import (
    _first_syllabus_topics,
    _weakest_topics_with_attempts,
)

logger = logging.getLogger(__name__)

TOP_K_CANDIDATES = 10
DEFAULT_MAX_MARKS = 5


class QuestionCandidate(TypedDict):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int
    paper_ref: str
    topic: str
    used_generated_mark_scheme: bool


async def pick_question(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    board: str,
    topic_override: str | None = None,
) -> QuestionCandidate:
    """Pick a question for grading. Weakness-driven by default; topic_override skips selection."""
    topic = await _resolve_topic(db, student_id, subject, topic_override)

    candidates = await _retrieve_from_qdrant(board, subject, topic, TOP_K_CANDIDATES)
    if not candidates:
        # Broaden search: drop topic filter within same board+subject
        candidates = await _retrieve_from_qdrant(board, subject, None, TOP_K_CANDIDATES)

    # History-avoidance filter
    seen_ids = await _load_seen_question_ids(db, student_id, subject)
    filtered = [c for c in candidates if c["question_id"] not in seen_ids]
    if not filtered:
        logger.info("All candidates already graded by student; dropping history filter")
        filtered = candidates

    # Qdrant returned nothing (collection missing, 404, or genuinely empty for
    # this board/subject) — synthesize a full question via LLM. MVP fallback,
    # same principle as _generate_mark_scheme_llm. Follow-up: re-ingest Qdrant.
    if not filtered:
        logger.info("Qdrant returned no candidates; synthesizing question via LLM")
        question_text = await _generate_question_llm(topic, subject, board)
        mark_scheme_text, max_marks = await _generate_mark_scheme_llm(question_text)
        import hashlib
        q_id = hashlib.md5(question_text[:200].encode()).hexdigest()[:16]
        return {
            "question_id": q_id,
            "question_text": question_text,
            "mark_scheme": mark_scheme_text,
            "max_marks": max_marks,
            "paper_ref": "Alex-generated practice question",
            "topic": topic,
            "used_generated_mark_scheme": True,
        }
    picked = random.choice(filtered)

    # Fetch mark scheme
    mark_scheme_result = await _fetch_mark_scheme(picked["paper_ref"], picked["question_id"])
    used_generated = False
    if mark_scheme_result is None:
        logger.info("No paired mark scheme in Qdrant; generating via LLM")
        mark_scheme_text, max_marks = await _generate_mark_scheme_llm(picked["question_text"])
        used_generated = True
    else:
        mark_scheme_text, max_marks = mark_scheme_result

    return {
        "question_id": picked["question_id"],
        "question_text": picked["question_text"],
        "mark_scheme": mark_scheme_text,
        "max_marks": max_marks,
        "paper_ref": picked["paper_ref"],
        "topic": picked.get("topic", topic),
        "used_generated_mark_scheme": used_generated,
    }


# ── topic resolution ────────────────────────────────────────────────────────

async def _resolve_topic(
    db: AsyncSession, student_id: UUID, subject: str, topic_override: str | None
) -> str:
    if topic_override:
        return topic_override
    weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=1)
    if weak:
        return weak[0][0]
    # Fresh student — first syllabus topic
    fallback = await _first_syllabus_topics(
        db, student_id, subject, exclude=set(), limit=1
    )
    if fallback:
        return fallback[0]
    raise RuntimeError("No topics available")


# ── Qdrant retrieval ────────────────────────────────────────────────────────

async def _retrieve_from_qdrant(
    board: str, subject: str, topic: str | None, top_k: int
) -> list[dict]:
    """Retrieve past-paper question chunks from Qdrant.

    Uses the qdrant_retriever with doc_type filter for past_paper.
    Payload schema: {text, source_file, exam_board, subject, exam_level, doc_type, year}.
    Note: no paper_ref or question_id fields in the current ingestion schema.
    Returns list of {question_id, question_text, paper_ref, topic}.
    """
    from app.rag.qdrant_retriever import retrieve

    query_text = topic.replace("_", " ") if topic else subject.replace("_", " ")

    hits = await retrieve(
        query=query_text,
        subject=subject,
        exam_board=board,
        exam_level="a_level",
        n_results=top_k,
        doc_types=["past_paper"],
    )
    results = []
    for hit in hits:
        # qdrant_retriever returns dicts with keys: text, source, score, metadata
        payload = hit.get("metadata", hit)
        text = hit.get("text", payload.get("text", ""))
        source = hit.get("source", payload.get("source_file", "Unknown"))
        year = payload.get("year", "unknown")
        paper_ref = f"{board.title()} {subject} {year}"
        # Generate a stable question_id from the text hash
        import hashlib
        q_id = hashlib.md5(text[:200].encode()).hexdigest()[:16]
        results.append({
            "question_id": q_id,
            "question_text": text,
            "paper_ref": paper_ref,
            "topic": topic or subject,
        })
    return results


async def _fetch_mark_scheme(paper_ref: str, question_id: str) -> tuple[str, int] | None:
    """Look up the mark scheme chunk that pairs with the given question.

    In the current ingestion schema, chunks lack question_id / paper_ref pairing
    metadata. This function attempts retrieval by doc_type=mark_scheme but cannot
    reliably match to a specific question — returns None in most production cases.
    LLM fallback (_generate_mark_scheme_llm) is what runs in practice.
    """
    from app.rag.qdrant_retriever import retrieve

    hits = await retrieve(
        query=paper_ref,
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
        n_results=5,
        doc_types=["mark_scheme"],
    )
    for hit in hits:
        payload = hit.get("metadata", hit)
        # No reliable pairing without question_id in payload; skip
        stored_q_id = str(payload.get("question_id", ""))
        linked_q_id = str(payload.get("linked_question_id", ""))
        if stored_q_id == question_id or linked_q_id == question_id:
            text = hit.get("text", payload.get("text", ""))
            max_marks = await _extract_max_marks(text)
            return text, max_marks
    return None


# ── mark scheme generation fallback ────────────────────────────────────────

async def _generate_question_llm(topic: str, subject: str, board: str) -> str:
    """Synthesize an A-Level practice question when Qdrant has no candidates."""
    topic_h = topic.replace("_", " ")
    subject_h = subject.replace("_", " ")
    prompt = f"""You are an A-Level {subject_h} examiner writing a single practice question.

Topic: {topic_h}
Board style: {board.title()} A-Level

Write ONE exam-style question of moderate difficulty (3–6 marks). Match the tone
and structure of a real past paper. Include the mark allocation in [X marks]
at the end. Return only the question text — no preamble, no solutions."""
    return await llm.generate(prompt)


async def _generate_mark_scheme_llm(question_text: str) -> tuple[str, int]:
    """Generate a mark scheme via LLM when Qdrant pairing is unavailable."""
    prompt = f"""You are an A-Level maths mark scheme writer.

Question:
{question_text}

Write a mark scheme showing how each mark is awarded. Use M1 (method), A1
(accuracy), B1 (independent) codes. Include the total mark count at the end
in the format: "Total: X marks".

Return only the mark scheme text, no commentary."""

    response = await llm.generate(prompt)
    max_marks = await _extract_max_marks(response)
    return response, max_marks


# ── max_marks extraction ───────────────────────────────────────────────────

_MARKS_REGEXES = [
    re.compile(r"Total:?\s*(\d+)\s*marks?", re.IGNORECASE),
    re.compile(r"\[(\d+)\s*marks?\]", re.IGNORECASE),
]


def _extract_max_marks_from_text(text: str) -> int | None:
    for regex in _MARKS_REGEXES:
        m = regex.search(text)
        if m:
            return int(m.group(1))
    return None


async def _extract_max_marks_via_llm(mark_scheme_text: str) -> int:
    prompt = (
        "Return only an integer — the total mark count for this mark scheme. "
        "No other text.\n\n" + mark_scheme_text
    )
    response = await llm.generate(prompt)
    match = re.search(r"\d+", response)
    if match:
        return int(match.group(0))
    raise ValueError("LLM did not return an integer")


async def _extract_max_marks(mark_scheme_text: str) -> int:
    regex_hit = _extract_max_marks_from_text(mark_scheme_text)
    if regex_hit is not None:
        return regex_hit
    try:
        return await _extract_max_marks_via_llm(mark_scheme_text)
    except Exception as exc:
        logger.warning("max_marks extraction failed: %s — defaulting to %d",
                       exc, DEFAULT_MAX_MARKS)
        return DEFAULT_MAX_MARKS


# ── history-avoidance ──────────────────────────────────────────────────────

async def _load_seen_question_ids(
    db: AsyncSession, student_id: UUID, subject: str
) -> set[str]:
    res = await db.execute(
        select(GradedUpload.question_id).where(
            GradedUpload.student_id == student_id,
            GradedUpload.subject == subject,
        )
    )
    return {row[0] for row in res.all()}
