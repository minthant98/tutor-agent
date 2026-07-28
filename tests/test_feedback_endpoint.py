"""
Tests for POST /api/v1/feedback
"""
import pytest


@pytest.mark.asyncio
async def test_feedback_returns_200_for_authed_user(authed_client):
    r = await authed_client.post(
        "/api/v1/feedback",
        json={"subject": "Bug report", "body": "Session page crashed on me."},
    )
    assert r.status_code == 200
    assert r.json() == {"status": "received"}


@pytest.mark.asyncio
async def test_feedback_requires_auth(unauth_client):
    r = await unauth_client.post(
        "/api/v1/feedback",
        json={"subject": "Test", "body": "No auth header here."},
    )
    assert r.status_code == 401
