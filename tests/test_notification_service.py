# tests/test_notification_service.py
import pytest
from uuid import uuid4
from app.services import notification_service as svc

@pytest.mark.asyncio
async def test_emit_creates_notification(db_session, student):
    n = await svc.emit(db_session, student.id, "readiness_increased",
                       payload={"subject": "pure_mathematics", "delta": 4.0})
    assert n.type == "readiness_increased"
    assert n.payload["delta"] == 4.0
    assert n.read_at is None

@pytest.mark.asyncio
async def test_list_returns_unread_first_newest_first(db_session, student):
    a = await svc.emit(db_session, student.id, "diagnostic_complete")
    b = await svc.emit(db_session, student.id, "readiness_increased")
    rows = await svc.list_recent(db_session, student.id)
    assert rows[0].id == b.id  # newest first
    assert rows[1].id == a.id

@pytest.mark.asyncio
async def test_mark_read(db_session, student):
    n = await svc.emit(db_session, student.id, "session_reminder")
    count = await svc.mark_read(db_session, student.id, [n.id])
    assert count == 1
    await db_session.refresh(n)
    assert n.read_at is not None

@pytest.mark.asyncio
async def test_unread_count(db_session, student):
    await svc.emit(db_session, student.id, "session_reminder")
    await svc.emit(db_session, student.id, "diagnostic_complete")
    assert await svc.unread_count(db_session, student.id) == 2
    await svc.mark_all_read(db_session, student.id)
    assert await svc.unread_count(db_session, student.id) == 0
