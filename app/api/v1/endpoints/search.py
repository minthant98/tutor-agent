"""
app/api/v1/endpoints/search.py
-----------------------------------
GET /api/v1/search?q=<query>&context=<topic_id|null>

Context-aware search over SyllabusTopic rows and recent GradedUpload submissions.
When `context` is provided, items whose topic_id matches are ranked first.

Field mapping (real model names):
  SyllabusTopic.topic_name  → label (brief uses "label" but real field is topic_name)
  SyllabusTopic.subject     → subtitle (brief uses "subject_label" but real field is subject)
  GradedUpload.subject      → topic_id proxy (no "topic" field exists on GradedUpload)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import GradedUpload, LearnerSubject, Student, SyllabusTopic

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str,
    context: str | None = None,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> list[dict[str, Any]]:
    """Return topic matches + recent graded submissions, context-ranked."""
    q_lower = q.lower().strip()
    results: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 1. Fetch the student's active (non-draft) subjects so we can scope
    #    syllabus topic results to what this student actually studies.
    # ------------------------------------------------------------------
    active_subjects_rows = (
        await db.execute(
            select(LearnerSubject.subject, LearnerSubject.syllabus_version).where(
                LearnerSubject.student_id == student.id,
                LearnerSubject.is_draft == False,  # noqa: E712
            )
        )
    ).all()

    # ------------------------------------------------------------------
    # 2. Topic matches — search across all the student's active subjects
    # ------------------------------------------------------------------
    if active_subjects_rows:
        subject_conditions = [
            (LearnerSubject.subject == row.subject)
            for row in active_subjects_rows
        ]

        for row in active_subjects_rows:
            topic_rows = (
                await db.execute(
                    select(SyllabusTopic).where(
                        SyllabusTopic.subject == row.subject,
                        SyllabusTopic.version == row.syllabus_version,
                        or_(
                            func.lower(SyllabusTopic.topic_id).contains(q_lower),
                            func.lower(SyllabusTopic.topic_name).contains(q_lower),
                        ),
                    ).order_by(SyllabusTopic.ordinal).limit(10)
                )
            ).scalars().all()

            for t in topic_rows:
                results.append(
                    {
                        "id": f"topic:{t.topic_id}",
                        "type": "topic",
                        "label": t.topic_name,
                        "subtitle": t.subject,
                        "href": f"/topics/{t.topic_id}",
                        "topic_id": t.topic_id,
                    }
                )
    else:
        # Fallback: search all topics if student has no subjects configured yet
        topic_rows = (
            await db.execute(
                select(SyllabusTopic).where(
                    or_(
                        func.lower(SyllabusTopic.topic_id).contains(q_lower),
                        func.lower(SyllabusTopic.topic_name).contains(q_lower),
                    ),
                ).order_by(SyllabusTopic.ordinal).limit(10)
            )
        ).scalars().all()

        for t in topic_rows:
            results.append(
                {
                    "id": f"topic:{t.topic_id}",
                    "type": "topic",
                    "label": t.topic_name,
                    "subtitle": t.subject,
                    "href": f"/topics/{t.topic_id}",
                    "topic_id": t.topic_id,
                }
            )

    # ------------------------------------------------------------------
    # 3. Recent graded submissions (up to 5)
    #    GradedUpload has no "topic" field — use "subject" as topic_id
    #    proxy for context-ranking purposes.
    # ------------------------------------------------------------------
    sub_rows = (
        await db.execute(
            select(GradedUpload).where(
                GradedUpload.student_id == student.id,
                GradedUpload.status == "graded",
            ).order_by(GradedUpload.created_at.desc()).limit(5)
        )
    ).scalars().all()

    for s in sub_rows:
        marks = (
            f"{s.marks_awarded}/{s.max_marks}"
            if s.marks_awarded is not None
            else f"/{s.max_marks}"
        )
        results.append(
            {
                "id": f"submission:{s.id}",
                "type": "submission",
                "label": s.question_text[:80],
                "subtitle": marks,
                "href": f"/mark/{s.id}",
                # Use subject as topic_id proxy for context-aware ranking
                "topic_id": s.subject,
            }
        )

    # ------------------------------------------------------------------
    # 4. Context-aware reranking — stable sort: context matches first
    # ------------------------------------------------------------------
    if context:
        results.sort(key=lambda r: (0 if r.get("topic_id") == context else 1))

    return results
