# app/services/notification_service.py
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Notification


async def emit(db: AsyncSession, student_id: UUID, type: str,
               payload: dict | None = None) -> Notification:
    # Set created_at explicitly (Python-side) so rapid successive emits within
    # the same DB transaction get distinct timestamps for correct ordering.
    n = Notification(
        student_id=student_id,
        type=type,
        payload=payload or {},
        created_at=datetime.now(timezone.utc),
    )
    db.add(n)
    await db.flush()
    return n


async def list_recent(db: AsyncSession, student_id: UUID, limit: int = 20) -> list[Notification]:
    res = await db.execute(
        select(Notification)
        .where(Notification.student_id == student_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list(res.scalars().all())


async def mark_read(db: AsyncSession, student_id: UUID, notification_ids: list[UUID]) -> int:
    now = datetime.now(timezone.utc)
    res = await db.execute(
        update(Notification)
        .where(Notification.student_id == student_id,
               Notification.id.in_(notification_ids),
               Notification.read_at.is_(None))
        .values(read_at=now)
    )
    await db.flush()
    return res.rowcount or 0


async def mark_all_read(db: AsyncSession, student_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    res = await db.execute(
        update(Notification)
        .where(Notification.student_id == student_id,
               Notification.read_at.is_(None))
        .values(read_at=now)
    )
    await db.flush()
    return res.rowcount or 0


async def unread_count(db: AsyncSession, student_id: UUID) -> int:
    res = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.student_id == student_id,
            Notification.read_at.is_(None),
        )
    )
    return res.scalar() or 0
