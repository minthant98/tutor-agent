"""Alex observations with traceability.

Generates up to 3 weekly observations per student/subject backed by real
evidence (graded uploads, mastery state, session records).

Anti-hallucination guard: any LLM item whose trace_ref is not a key in
the evidence dict is silently dropped before persistence.

Three hard prompt rules (same as dashboard_narration):
1. NEVER praise
2. NEVER speculate
3. Always analytical — every claim must reference provided evidence
"""
import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm
from app.db.models import GradedUpload, MasteryState, Observation, TutorSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SYSTEM_INSTRUCTION — behavioral guard (tests assert its content)
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """You are Alex, an A-Level tutor writing brief weekly observations about a student's work.

HARD RULES:
1. NEVER praise. Do not say "great job", "well done", "amazing", "keep it up", "you're crushing it", "impressive". Analytical language only.
2. NEVER speculate. Every observation must reference specific data from the provided evidence.
3. Return a JSON array. Each element: {"text": "<one concise analytical sentence>", "trace_ref": "<one of the provided evidence keys>"}.
4. Maximum 3 items. If evidence is thin, return fewer or return [].
5. No exclamation marks. No emoji. Do not use the student's name."""


# ---------------------------------------------------------------------------
# Evidence types
# ---------------------------------------------------------------------------

class EvidenceItem:
    """Holds raw evidence for one traceable reference key."""

    def __init__(self, queries: list[str], session_ids: list[str], summary: str):
        self.queries = queries
        self.session_ids = session_ids
        self.summary = summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "queries": self.queries,
            "session_ids": self.session_ids,
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _week_start(for_date: date) -> date:
    """Return the Monday of the week containing for_date."""
    return for_date - timedelta(days=for_date.weekday())


async def _gather_evidence(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    week_of: date,
) -> dict[str, Any]:
    """Gather evidence from mastery state and graded uploads.

    Returns {"items": {ref_key: EvidenceItem, ...}} for LLM consumption.
    """
    week_start = _week_start(week_of)
    week_end = week_start + timedelta(days=7)

    # ------------------------------------------------------------------ #
    # Query 1: mastery delta — topics with is_weak flag or recent review  #
    # ------------------------------------------------------------------ #
    weak_mastery_rows = (
        await db.execute(
            select(MasteryState)
            .where(
                MasteryState.student_id == student_id,
                MasteryState.subject == subject,
            )
            .order_by(MasteryState.mastery_score.asc())
            .limit(10)
        )
    ).scalars().all()

    # ------------------------------------------------------------------ #
    # Query 2: graded uploads this week                                   #
    # ------------------------------------------------------------------ #
    week_start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    week_end_dt = datetime(week_end.year, week_end.month, week_end.day, tzinfo=timezone.utc)

    upload_rows = (
        await db.execute(
            select(GradedUpload)
            .where(
                GradedUpload.student_id == student_id,
                GradedUpload.subject == subject,
                GradedUpload.status == "graded",
                GradedUpload.created_at >= week_start_dt,
                GradedUpload.created_at < week_end_dt,
            )
            .order_by(GradedUpload.created_at.desc())
            .limit(20)
        )
    ).scalars().all()

    # ------------------------------------------------------------------ #
    # Query 3: sessions this week                                         #
    # ------------------------------------------------------------------ #
    session_rows = (
        await db.execute(
            select(TutorSession)
            .where(
                TutorSession.student_id == student_id,
                TutorSession.subject == subject,
                TutorSession.started_at >= week_start_dt,
                TutorSession.started_at < week_end_dt,
            )
            .order_by(TutorSession.started_at.desc())
            .limit(20)
        )
    ).scalars().all()

    # ------------------------------------------------------------------ #
    # Build evidence items                                                #
    # ------------------------------------------------------------------ #
    items: dict[str, EvidenceItem] = {}

    # Evidence A: weak mastery topics (if any are notably weak)
    weak_topics = [
        r for r in weak_mastery_rows if r.is_weak or r.mastery_score < 0.4
    ]
    if weak_topics:
        topic_summaries = [
            f"{r.topic}: mastery={r.mastery_score:.2f}, streak={r.correct_streak}"
            for r in weak_topics[:3]
        ]
        items["mastery_weak_topics"] = EvidenceItem(
            queries=["mastery_delta_last_7d"],
            session_ids=[],
            summary="Weak mastery topics: " + "; ".join(topic_summaries),
        )

    # Evidence B: graded upload performance this week
    if upload_rows:
        graded_ids = [str(r.id) for r in upload_rows]
        avg_grade = sum(float(r.grade_pct or 0) for r in upload_rows) / len(upload_rows)
        topic_names = list({r.question_id.split("_")[0] for r in upload_rows if r.question_id})
        items["graded_uploads_this_week"] = EvidenceItem(
            queries=["graded_uploads_this_week"],
            session_ids=graded_ids,
            summary=(
                f"{len(upload_rows)} graded attempt(s) this week, "
                f"avg grade {avg_grade:.1f}%. "
                f"Topics touched: {', '.join(topic_names[:3]) if topic_names else 'various'}."
            ),
        )

    # Evidence C: session volume / topics this week
    if session_rows:
        session_ids = [str(r.id) for r in session_rows]
        topics_covered = list({r.topic for r in session_rows if r.topic})
        items["sessions_this_week"] = EvidenceItem(
            queries=["sessions_this_week"],
            session_ids=session_ids,
            summary=(
                f"{len(session_rows)} session(s) this week. "
                f"Topics: {', '.join(topics_covered[:5]) if topics_covered else 'not recorded'}."
            ),
        )

    # Evidence D: low mastery trend across subject (no sessions this week but mastery data exists)
    if not session_rows and not upload_rows and weak_mastery_rows:
        all_scores = [r.mastery_score for r in weak_mastery_rows]
        avg_score = sum(all_scores) / len(all_scores)
        items["subject_mastery_baseline"] = EvidenceItem(
            queries=["mastery_delta_last_7d"],
            session_ids=[],
            summary=(
                f"No activity this week. Subject avg mastery={avg_score:.2f} "
                f"across {len(weak_mastery_rows)} topic(s)."
            ),
        )

    return {"items": items}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_for_week(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    week_of: date,
) -> list[Observation]:
    """Generate and persist up to 3 observations for (student, subject, week_of).

    Returns the list of persisted Observation rows (may be empty).
    Does NOT commit — caller owns the transaction.
    """
    evidence = await _gather_evidence(db, student_id, subject, week_of)

    if not evidence["items"]:
        return []

    # Serialize evidence for LLM prompt
    llm_evidence: dict[str, Any] = {
        ref: item.to_dict() for ref, item in evidence["items"].items()
    }

    prompt = (
        f"Evidence keys available: {list(llm_evidence.keys())}\n\n"
        f"Evidence:\n{json.dumps(llm_evidence, indent=2)}\n\n"
        "Write up to 3 observations about what this student did this week. "
        "Return a JSON array only."
    )

    try:
        response = await llm.generate_json(prompt, system=SYSTEM_INSTRUCTION)
    except Exception as exc:
        logger.error("LLM failed generating observations: %s", exc)
        return []

    obs_list = response if isinstance(response, list) else response.get("observations", [])

    saved: list[Observation] = []
    for item in obs_list[:3]:  # hard cap — LLM may ignore instruction
        if not isinstance(item, dict):
            continue
        ref = item.get("trace_ref", "")
        ev = evidence["items"].get(ref)
        if not ev:
            # Anti-hallucination: drop items with unknown trace_ref
            logger.warning("Dropping observation with unknown trace_ref=%r", ref)
            continue
        text_val = (item.get("text") or "").strip()
        if not text_val:
            continue
        obs = Observation(
            student_id=student_id,
            subject=subject,
            text=text_val[:500],
            trace_json={
                "queries": ev.queries,
                "session_ids": ev.session_ids,
                "evidence_summary": ev.summary,
            },
            week_of=week_of,
        )
        saved.append(obs)

    # Enforce hard cap of 3 after filtering
    saved = saved[:3]

    if saved:
        db.add_all(saved)
        await db.flush()

    return saved
