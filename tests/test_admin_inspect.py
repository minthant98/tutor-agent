"""Tests for admin inspect endpoint (Task 19)."""
import pytest


@pytest.mark.asyncio
async def test_inspect_requires_admin(authed_client, student_with_subject):
    """Non-admin student should receive 403."""
    r = await authed_client.get(
        f"/api/v1/admin/students/{student_with_subject.id}/inspect"
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_inspect(admin_authed_client, student_with_subject):
    """Admin student can inspect any student's profile."""
    r = await admin_authed_client.get(
        f"/api/v1/admin/students/{student_with_subject.id}/inspect"
    )
    assert r.status_code == 200
    body = r.json()
    assert "profile" in body
    assert "subjects" in body
    assert "mastery" in body


@pytest.mark.asyncio
async def test_admin_inspect_structure(admin_authed_client, student_with_subject):
    """Inspect response has all expected top-level keys."""
    r = await admin_authed_client.get(
        f"/api/v1/admin/students/{student_with_subject.id}/inspect"
    )
    assert r.status_code == 200
    body = r.json()
    assert "profile" in body
    assert "subjects" in body
    assert "mastery" in body
    assert "latest_today_focus" in body
    assert "active_session" in body
    assert "recent_sessions" in body
    # Profile has expected fields
    profile = body["profile"]
    assert "id" in profile
    assert "name" in profile
    assert "email" in profile


@pytest.mark.asyncio
async def test_admin_inspect_404_for_missing_student(admin_authed_client):
    """Inspect with a non-existent student_id should return 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    r = await admin_authed_client.get(f"/api/v1/admin/students/{fake_id}/inspect")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_inspect_returns_401(unauth_client, student_with_subject):
    """Unauthenticated request to inspect should return 401."""
    r = await unauth_client.get(
        f"/api/v1/admin/students/{student_with_subject.id}/inspect"
    )
    assert r.status_code == 401
