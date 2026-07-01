# app/api/v1/endpoints/notifications.py
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student
from app.services import notification_service as ns
from app.schemas.notifications import NotificationListOut, NotificationOut, MarkReadIn

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> NotificationListOut:
    items = await ns.list_recent(db, student.id)
    count = await ns.unread_count(db, student.id)
    return NotificationListOut(
        items=[
            NotificationOut(
                id=str(n.id),
                type=n.type,
                payload=n.payload,
                read_at=n.read_at,
                created_at=n.created_at,
            )
            for n in items
        ],
        unread_count=count,
    )


@router.post("/mark-read")
async def mark_read(
    body: MarkReadIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> dict:
    n = await ns.mark_read(db, student.id, [UUID(i) for i in body.ids])
    return {"marked": n}


@router.post("/mark-all-read")
async def mark_all_read(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> dict:
    n = await ns.mark_all_read(db, student.id)
    return {"marked": n}
