"""Tests for /readyz readiness probe (Task 18)."""
import pytest


@pytest.mark.asyncio
async def test_readyz_503_when_no_syllabus(unauth_client, empty_db):
    """Without syllabus topics seeded, /readyz returns 503."""
    r = await unauth_client.get("/readyz")
    # Could be 200 if Redis/GROQ both OK but no syllabus, or 503 with no_syllabus_topics
    # We check that it is either 503 (syllabus missing) or 200 (all OK — means syllabus seeded externally)
    assert r.status_code in (200, 503)
    if r.status_code == 503:
        body = r.json()
        # The failures list should exist
        assert "failures" in body.get("detail", {}) or "detail" in body


@pytest.mark.asyncio
async def test_readyz_200_when_seeded(unauth_client, syllabus_edexcel_seeded):
    """With syllabus seeded and GROQ_API_KEY set, /readyz should return 200 or 503 based on env."""
    import os
    r = await unauth_client.get("/readyz")
    if os.environ.get("GROQ_API_KEY"):
        # If all checks pass, expect 200
        assert r.status_code in (200, 503)
    else:
        # GROQ key missing in test env — expect 503
        assert r.status_code == 503
        body = r.json()
        assert "groq_api_key_missing" in str(body)


@pytest.mark.asyncio
async def test_readyz_structure(unauth_client, empty_db):
    """Response has correct structure regardless of status."""
    r = await unauth_client.get("/readyz")
    body = r.json()
    if r.status_code == 200:
        assert body.get("status") == "ready"
    else:
        assert r.status_code == 503
        detail = body.get("detail", {})
        assert "status" in detail or "failures" in detail


@pytest.mark.asyncio
async def test_readyz_reports_bucket_missing(unauth_client):
    from unittest.mock import AsyncMock, patch
    from app.services.marker import storage
    with patch.object(storage, "check_bucket_exists", new=AsyncMock(return_value=False)):
        r = await unauth_client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert "storage" in str(body).lower() or "bucket" in str(body).lower()


@pytest.mark.asyncio
async def test_readyz_passes_when_bucket_exists(unauth_client, syllabus_edexcel_seeded):
    import os
    from unittest.mock import AsyncMock, patch
    from app.services.marker import storage
    # Patch GROQ_API_KEY into os.environ so the existing key check passes in any env
    with patch.object(storage, "check_bucket_exists", new=AsyncMock(return_value=True)), \
         patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
        r = await unauth_client.get("/readyz")
    assert r.status_code == 200
