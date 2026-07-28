"""Tests for PATCH /api/v1/sessions/{session_id}/state

Task 14: Autosave — verifies that the endpoint:
  - Persists cursor + input_draft into session.state JSONB
  - Returns {"ok": true}
  - Merges (does not replace) on subsequent patches
  - Returns 403 for foreign sessions
"""
import pytest
import pytest_asyncio
import uuid as _uuid

from app.db.models import TutorSession


# ---------------------------------------------------------------------------
# Local fixture — a TutorSession row owned by student_with_subject
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def owned_session(db_session, student_with_subject):
    """A TutorSession row owned by student_with_subject."""
    sess = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="practice",
        segment_plan=[],
    )
    db_session.add(sess)
    await db_session.flush()
    return sess


@pytest_asyncio.fixture
async def other_session(db_session):
    """A TutorSession row owned by a different student (for 403 test)."""
    from app.db.models import Student
    other = Student(
        email=f"other_{_uuid.uuid4().hex[:8]}@example.com",
        name="Other Student",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=False,
    )
    db_session.add(other)
    await db_session.flush()

    sess = TutorSession(
        student_id=other.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="practice",
        segment_plan=[],
    )
    db_session.add(sess)
    await db_session.flush()
    return sess


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_state_persists_cursor(
    authed_client, student_with_subject, owned_session
):
    """PATCH saves cursor and input_draft; GET returns them."""
    r = await authed_client.patch(
        f"/api/v1/sessions/{owned_session.id}/state",
        json={
            "cursor": {"segment_index": 1, "block_index": 3},
            "input_draft": "so far...",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    r2 = await authed_client.get(f"/api/v1/sessions/{owned_session.id}")
    body = r2.json()
    assert body["state"]["cursor"]["segment_index"] == 1
    assert body["state"]["cursor"]["block_index"] == 3
    assert body["state"]["input_draft"] == "so far..."


@pytest.mark.asyncio
async def test_patch_state_merge_preserves_prior_fields(
    authed_client, student_with_subject, owned_session
):
    """Second PATCH with only input_draft must not wipe cursor from first PATCH."""
    # First patch — set cursor
    r1 = await authed_client.patch(
        f"/api/v1/sessions/{owned_session.id}/state",
        json={"cursor": {"segment_index": 2, "block_index": 0}},
    )
    assert r1.status_code == 200

    # Second patch — only input_draft; cursor must survive
    r2 = await authed_client.patch(
        f"/api/v1/sessions/{owned_session.id}/state",
        json={"input_draft": "updated draft"},
    )
    assert r2.status_code == 200

    r3 = await authed_client.get(f"/api/v1/sessions/{owned_session.id}")
    body = r3.json()
    assert body["state"]["cursor"]["segment_index"] == 2, "cursor was wiped by second PATCH"
    assert body["state"]["input_draft"] == "updated draft"


@pytest.mark.asyncio
async def test_patch_state_foreign_session_returns_403(
    authed_client, student_with_subject, other_session
):
    """Patching a session owned by another student must return 403."""
    r = await authed_client.patch(
        f"/api/v1/sessions/{other_session.id}/state",
        json={"cursor": {"segment_index": 0, "block_index": 0}},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_patch_state_nonexistent_session_returns_404(
    authed_client, student_with_subject
):
    """Patching a session that doesn't exist must return 404."""
    fake_id = _uuid.uuid4()
    r = await authed_client.patch(
        f"/api/v1/sessions/{fake_id}/state",
        json={"input_draft": "hello"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_state_empty_body_is_noop(
    authed_client, student_with_subject, owned_session
):
    """Empty PATCH body (no fields) must not wipe existing state."""
    # Prime some state
    await authed_client.patch(
        f"/api/v1/sessions/{owned_session.id}/state",
        json={"cursor": {"segment_index": 5, "block_index": 1}},
    )

    # Patch with no meaningful fields
    r = await authed_client.patch(
        f"/api/v1/sessions/{owned_session.id}/state",
        json={},
    )
    assert r.status_code == 200

    r2 = await authed_client.get(f"/api/v1/sessions/{owned_session.id}")
    body = r2.json()
    assert body["state"]["cursor"]["segment_index"] == 5, "state was wiped by empty PATCH"
