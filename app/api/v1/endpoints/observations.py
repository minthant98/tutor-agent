"""app/api/v1/endpoints/observations.py
---------------------------------------
GET /api/v1/observations/current-week?subject=<subject>

Returns up to 3 Alex observations for the current week.
Cache-hit: if rows already exist for (student, subject, week_of), returns them.
Cache-miss: generates via service, persists, returns.

trace_json is NOT exposed in the API response — it is server-side plumbing
for a future "why did Alex say that?" affordance.
"""
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Observation, Student
from app.services.narration import observations as obs_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observations", tags=["observations"])


def _current_week_start() -> date:
    """Return the Monday of the current week (ISO week convention)."""
    today = date.today()
    return today - timedelta(days=today.weekday())


class ObservationOut(BaseModel):
    id: str
    text: str
    computed_at: str

    model_config = {"from_attributes": True}


@router.get("/current-week", response_model=list[ObservationOut])
async def get_current_week_observations(
    subject: str = Query(..., description="Subject slug, e.g. pure_mathematics"),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Return this week's observations for the authenticated student + subject.

    If observations already exist for (student, subject, week_of), they are
    returned immediately (cache-hit). Otherwise, the service is called to
    generate and persist them (cache-miss).
    """
    week_of = _current_week_start()

    # Cache-hit check
    existing = (
        await db.execute(
            select(Observation)
            .where(
                Observation.student_id == student.id,
                Observation.subject == subject,
                Observation.week_of == week_of,
            )
            .order_by(Observation.computed_at.asc())
        )
    ).scalars().all()

    if existing:
        return [
            ObservationOut(
                id=str(o.id),
                text=o.text,
                computed_at=o.computed_at.isoformat(),
            )
            for o in existing
        ]

    # Cache-miss: generate
    generated = await obs_service.generate_for_week(db, student.id, subject, week_of)
    await db.commit()

    return [
        ObservationOut(
            id=str(o.id),
            text=o.text,
            computed_at=o.computed_at.isoformat(),
        )
        for o in generated
    ]
