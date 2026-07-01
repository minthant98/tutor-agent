"""Tests for notifications endpoints (Task 18)."""
import pytest


@pytest.mark.asyncio
async def test_list_notifications_empty(authed_client, student_with_subject):
    """GET /api/v1/notifications returns empty list for new student."""
    r = await authed_client.get("/api/v1/notifications")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "unread_count" in body
    assert body["unread_count"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_list_notifications_returns_after_emit(authed_client, student_with_subject, db_session):
    """After emitting a notification, list returns it."""
    from app.services import notification_service as ns
    await ns.emit(db_session, student_with_subject.id, "test_event", {"msg": "hello"})

    r = await authed_client.get("/api/v1/notifications")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1
    assert body["unread_count"] == 1
    assert body["items"][0]["type"] == "test_event"


@pytest.mark.asyncio
async def test_mark_read(authed_client, student_with_subject, db_session):
    """POST /api/v1/notifications/mark-read marks a notification as read."""
    from app.services import notification_service as ns
    n = await ns.emit(db_session, student_with_subject.id, "test_event", {"msg": "hello"})

    r = await authed_client.post(
        "/api/v1/notifications/mark-read",
        json={"ids": [str(n.id)]},
    )
    assert r.status_code == 200
    assert r.json()["marked"] == 1


@pytest.mark.asyncio
async def test_mark_all_read(authed_client, student_with_subject, db_session):
    """POST /api/v1/notifications/mark-all-read marks all notifications as read."""
    from app.services import notification_service as ns
    await ns.emit(db_session, student_with_subject.id, "event_1", {})
    await ns.emit(db_session, student_with_subject.id, "event_2", {})

    r = await authed_client.post("/api/v1/notifications/mark-all-read")
    assert r.status_code == 200
    assert r.json()["marked"] == 2


@pytest.mark.asyncio
async def test_notifications_requires_auth(unauth_client):
    """Without auth, notifications list should return 401."""
    r = await unauth_client.get("/api/v1/notifications")
    assert r.status_code == 401
