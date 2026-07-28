"""Nightly progress narration refresh job.

Scheduled at 03:00 UTC daily (infra concern — see railway.toml or cron config).
Runs for each active student × subject; upserts today's narration row.

Usage (manual):
    python -m app.jobs.progress_narration_refresh

Idempotent: running twice on the same day is safe (INSERT ON CONFLICT UPDATE).
"""
import asyncio
import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.models import LearnerSubject, MasteryState, ProgressNarration, ReadinessSnapshot, Student
from app.services.narration import progress_narration

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _build_context(
    db: AsyncSession,
    student_id,
    subject: str,
) -> dict:
    """Assemble the narration context for a given student/subject."""
    today = date.today()
    cutoff = today - timedelta(days=14)

    # Readiness series — last 14 days
    snap_rows = (
        await db.execute(
            select(ReadinessSnapshot.snapshot_date, ReadinessSnapshot.readiness_pct)
            .where(
                ReadinessSnapshot.student_id == student_id,
                ReadinessSnapshot.subject == subject,
                ReadinessSnapshot.snapshot_date >= cutoff,
            )
            .order_by(ReadinessSnapshot.snapshot_date)
        )
    ).all()

    readiness_series = [(r.snapshot_date, int(round(r.readiness_pct))) for r in snap_rows]

    # Mastery states for top gainer / slipper
    m_rows = (
        await db.execute(
            select(MasteryState.topic, MasteryState.mastery_score).where(
                MasteryState.student_id == student_id,
                MasteryState.subject == subject,
            )
        )
    ).all()

    # Simple heuristic: sort by mastery_score desc for gainer, asc for slipper
    sorted_by_score = sorted(m_rows, key=lambda r: r.mastery_score or 0.0, reverse=True)
    top_gainer = sorted_by_score[0].topic if sorted_by_score else None
    top_slipper = sorted_by_score[-1].topic if len(sorted_by_score) > 1 else None

    return {
        "readiness_series": readiness_series,
        "top_gainer": top_gainer,
        "top_slipper": top_slipper,
    }


async def _upsert_narration(
    db: AsyncSession,
    student_id,
    subject: str,
    text: str,
    computed_date: date,
) -> None:
    """INSERT or UPDATE today's narration row (idempotent, atomic ON CONFLICT upsert)."""
    stmt = (
        pg_insert(ProgressNarration)
        .values(
            id=uuid.uuid4(),
            student_id=student_id,
            subject=subject,
            computed_date=computed_date,
            text=text,
        )
        .on_conflict_do_update(
            index_elements=["student_id", "subject", "computed_date"],
            set_={"text": text, "computed_at": func.now()},
        )
    )
    await db.execute(stmt)
    await db.commit()


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------


async def run() -> None:
    """Process all active student×subject pairs and upsert today's narration."""
    today = date.today()
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as db:
        # Active students: subscription_status == 'active'
        student_rows = (
            await db.execute(
                select(Student.id).where(Student.subscription_status == "active")
            )
        ).scalars().all()

        logger.info("Found %d active students", len(student_rows))

        for student_id in student_rows:
            # Subjects enrolled (non-draft LearnerSubject rows)
            subject_rows = (
                await db.execute(
                    select(LearnerSubject.subject).where(
                        LearnerSubject.student_id == student_id,
                        LearnerSubject.is_draft == False,  # noqa: E712
                    )
                )
            ).scalars().all()

            for subject in subject_rows:
                try:
                    ctx = await _build_context(db, student_id, subject)
                    narration_text = await progress_narration.generate(ctx)
                    # Trim to 500 chars (model constraint)
                    narration_text = narration_text[:500]
                    await _upsert_narration(db, student_id, subject, narration_text, today)
                    logger.info(
                        "Narration upserted for student=%s subject=%s date=%s",
                        student_id,
                        subject,
                        today,
                    )
                except Exception:
                    logger.exception(
                        "Failed to generate narration for student=%s subject=%s",
                        student_id,
                        subject,
                    )

    await engine.dispose()
    logger.info("progress_narration_refresh complete for %s", today)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
