# app/services/readiness_service.py
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MasteryState, SyllabusTopic, ReadinessSnapshot

COMPETENT_THRESHOLD = 0.7


async def _get_exam_board(db: AsyncSession, student_id: UUID, subject: str) -> str | None:
    """Return the exam board the student is registered for, or None if not found."""
    from app.db.models import LearnerSubject, Student
    ls = await db.execute(
        select(LearnerSubject.exam_board).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    board = ls.scalar()
    if board:
        return board
    # Fallback to the legacy flat field on Student
    student = await db.get(Student, student_id)
    return student.exam_board if student else None


async def compute_readiness_pct(db: AsyncSession, student_id: UUID, subject: str, version: str) -> float:
    exam_board = await _get_exam_board(db, student_id, subject)

    where_clauses = [
        SyllabusTopic.subject == subject,
        SyllabusTopic.version == version,
    ]
    if exam_board:
        where_clauses.append(SyllabusTopic.exam_board == exam_board)

    total_q = select(func.count(SyllabusTopic.id)).where(*where_clauses)
    total = (await db.execute(total_q)).scalar() or 0
    if total == 0:
        return 0.0

    topic_ids_q = select(SyllabusTopic.topic_id).where(*where_clauses)
    topic_ids = {r[0] for r in (await db.execute(topic_ids_q)).all()}

    mastery_q = select(MasteryState.topic, MasteryState.mastery_score).where(
        MasteryState.student_id == student_id,
        MasteryState.subject == subject,
    )
    competent = 0
    for topic, score in (await db.execute(mastery_q)).all():
        if topic in topic_ids and (score or 0) >= COMPETENT_THRESHOLD:
            competent += 1
    return round(100.0 * competent / total, 1)


async def write_snapshot_if_first_today(db: AsyncSession, student_id: UUID, subject: str) -> ReadinessSnapshot | None:
    today = date.today()
    existing = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date == today,
        )
    )
    if existing.scalar_one_or_none():
        return None
    # Use the student's pinned syllabus version
    from app.db.models import LearnerSubject
    ls = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = ls.scalar() or "2026.1"
    pct = await compute_readiness_pct(db, student_id, subject, version)
    snap = ReadinessSnapshot(
        student_id=student_id, subject=subject,
        snapshot_date=today, readiness_pct=pct,
    )
    db.add(snap)
    await db.flush()

    # Find yesterday's snapshot to compute delta for telemetry
    try:
        prev_row = (await db.execute(
            select(ReadinessSnapshot).where(
                ReadinessSnapshot.student_id == student_id,
                ReadinessSnapshot.subject == subject,
                ReadinessSnapshot.snapshot_date < today,
            ).order_by(ReadinessSnapshot.snapshot_date.desc()).limit(1)
        )).scalar_one_or_none()
        if prev_row and abs(snap.readiness_pct - prev_row.readiness_pct) > 0.1:
            from app.core.telemetry import capture
            delta = snap.readiness_pct - prev_row.readiness_pct
            capture(str(student_id), "readiness_changed", {
                "subject": subject,
                "prev_pct": prev_row.readiness_pct,
                "new_pct": snap.readiness_pct,
                "delta": delta,
            })
            if delta >= 1.0:
                from app.services.notification_service import emit
                await emit(db, student_id, "readiness_increased",
                           payload={"subject": subject, "delta": round(delta, 1)})
    except Exception:
        pass

    return snap


async def get_trend_vs_28d(db: AsyncSession, student_id: UUID, subject: str) -> dict | None:
    today = date.today()
    cutoff = today - timedelta(days=7)
    history_count = await db.execute(
        select(func.count(ReadinessSnapshot.id)).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date <= cutoff,
        )
    )
    if (history_count.scalar() or 0) < 1:
        return None  # gate: ≥7 days of history
    today_snap = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date == today,
        )
    )
    today_row = today_snap.scalar_one_or_none()
    if not today_row:
        return None
    past_cutoff = today - timedelta(days=28)
    past = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date <= past_cutoff,
        ).order_by(ReadinessSnapshot.snapshot_date.desc()).limit(1)
    )
    past_row = past.scalar_one_or_none()
    if not past_row:
        return None
    return {
        "prev_pct": past_row.readiness_pct,
        "new_pct": today_row.readiness_pct,
        "delta": round(today_row.readiness_pct - past_row.readiness_pct, 1),
    }
