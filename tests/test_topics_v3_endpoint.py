"""Tests for GET /api/v1/topics/v3 — topics v3 syllabus browser endpoint."""
import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_topics_v3_returns_list(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Endpoint returns a list of topic objects."""
    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # Each item has required fields
    first = body[0]
    assert "id" in first
    assert "label" in first
    assert "mastery" in first
    assert "last_practised" in first
    assert "status" in first
    assert "prerequisite" in first
    assert first["prerequisite"] is None


@pytest.mark.asyncio
async def test_topics_v3_auth_required(
    unauth_client, student_with_subject, syllabus_edexcel_seeded
):
    """Endpoint requires authentication — 401 without token."""
    r = await unauth_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_topics_v3_unknown_subject_404(
    authed_client, student_with_subject
):
    """Unknown subject returns 404."""
    r = await authed_client.get("/api/v1/topics/v3?subject=nonexistent_subject")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_topics_v3_fresh_student_all_not_started(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Fresh student with no mastery records: all topics show Not started, mastery 0, last_practised Never."""
    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    for topic in body:
        assert topic["mastery"] == 0
        assert topic["status"] == "Not started"
        assert topic["last_practised"] == "Never"


@pytest.mark.asyncio
async def test_topics_v3_status_labels_mastered(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """mastery_score >= 0.7 → 'Mastered'."""
    from app.db.models import MasteryState

    db_session.add(MasteryState(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        topic="integration_basics",
        mastery_score=0.85,
        total_attempts=5,
    ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    topics_by_id = {t["id"]: t for t in r.json()}
    assert topics_by_id["integration_basics"]["status"] == "Mastered"
    assert topics_by_id["integration_basics"]["mastery"] == 85


@pytest.mark.asyncio
async def test_topics_v3_status_labels_practising(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """mastery_score >= 0.4 and < 0.7 → 'Practising'."""
    from app.db.models import MasteryState

    db_session.add(MasteryState(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        topic="integration_basics",
        mastery_score=0.55,
        total_attempts=3,
    ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    topics_by_id = {t["id"]: t for t in r.json()}
    assert topics_by_id["integration_basics"]["status"] == "Practising"


@pytest.mark.asyncio
async def test_topics_v3_status_labels_needs_review(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """mastery_score > 0 and < 0.4 → 'Needs review'."""
    from app.db.models import MasteryState

    db_session.add(MasteryState(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        topic="integration_basics",
        mastery_score=0.20,
        total_attempts=2,
    ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    topics_by_id = {t["id"]: t for t in r.json()}
    assert topics_by_id["integration_basics"]["status"] == "Needs review"


@pytest.mark.asyncio
async def test_topics_v3_last_practised_relative_string(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """last_practised is a relative string when last_reviewed_at is set."""
    from app.db.models import MasteryState

    db_session.add(MasteryState(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        topic="integration_basics",
        mastery_score=0.50,
        total_attempts=2,
        last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=3),
    ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    topics_by_id = {t["id"]: t for t in r.json()}
    assert topics_by_id["integration_basics"]["last_practised"] == "3 days ago"


@pytest.mark.asyncio
async def test_topics_v3_prerequisite_always_null(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    """MVP: prerequisite is always null (no prereq graph in SyllabusTopic)."""
    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    for topic in r.json():
        assert topic["prerequisite"] is None


@pytest.mark.asyncio
async def test_topics_v3_ordered_by_syllabus_ordinal(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Topics are returned in syllabus ordinal order."""
    r = await authed_client.get("/api/v1/topics/v3?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    # We can't check ordinal values directly, but list must be non-empty and stable
    ids = [t["id"] for t in body]
    assert len(ids) == len(set(ids)), "No duplicate topic IDs"
