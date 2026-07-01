"""Tests for onboarding wizard endpoints (Task 16).

Uses `onboarding_client` (fresh student with no subjects) for wizard flow tests
so that `upsert_subject_draft` doesn't hit an existing finalized subject row.
"""
import pytest


@pytest.mark.asyncio
async def test_wizard_state_endpoint_exists(onboarding_client):
    """GET /api/v1/onboarding/state should return 200 with next_step and progress_pct."""
    r = await onboarding_client.get("/api/v1/onboarding/state")
    assert r.status_code == 200
    body = r.json()
    assert "next_step" in body
    assert "progress_pct" in body


@pytest.mark.asyncio
async def test_wizard_state_starts_at_subjects_when_no_drafts(onboarding_client):
    """Fresh student with no subjects: wizard should start at 'subjects'."""
    r = await onboarding_client.get("/api/v1/onboarding/state")
    assert r.status_code == 200
    body = r.json()
    assert body["next_step"] == "subjects"
    assert body["progress_pct"] == 0


@pytest.mark.asyncio
async def test_post_subjects_creates_drafts_and_advances(onboarding_client):
    """POST /api/v1/onboarding/subjects should create draft subjects and advance to exam-board."""
    r = await onboarding_client.post(
        "/api/v1/onboarding/subjects",
        json={"subjects": ["pure_mathematics"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["next_step"] == "exam-board"
    assert body["progress_pct"] > 0


@pytest.mark.asyncio
async def test_post_exam_board_marks_done_advances_to_exam_date(onboarding_client):
    """After subjects + exam-board steps, wizard advances to exam-date."""
    await onboarding_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    r = await onboarding_client.post("/api/v1/onboarding/exam-board", json={"exam_board": "edexcel"})
    assert r.status_code == 200
    assert r.json()["next_step"] == "exam-date"


@pytest.mark.asyncio
async def test_post_exam_date_advances_to_target_grade(onboarding_client):
    """After subjects + exam-board + exam-date steps, wizard advances to target-grade."""
    await onboarding_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    await onboarding_client.post("/api/v1/onboarding/exam-board", json={"exam_board": "edexcel"})
    r = await onboarding_client.post("/api/v1/onboarding/exam-date", json={"exam_date": "2027-05-01"})
    assert r.status_code == 200
    assert r.json()["next_step"] == "target-grade"


@pytest.mark.asyncio
async def test_post_target_grade_advances_to_preferences(onboarding_client):
    """After subjects+board+date+grade, wizard advances to preferences."""
    await onboarding_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    await onboarding_client.post("/api/v1/onboarding/exam-board", json={"exam_board": "edexcel"})
    await onboarding_client.post("/api/v1/onboarding/exam-date", json={"exam_date": "2027-05-01"})
    r = await onboarding_client.post("/api/v1/onboarding/target-grade", json={"target_grade": "A*"})
    assert r.status_code == 200
    assert r.json()["next_step"] == "preferences"


@pytest.mark.asyncio
async def test_post_preferences_preserves_step_markers(onboarding_client):
    """Posting preferences should not wipe _step_* markers; wizard advances to roadmap."""
    await onboarding_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    await onboarding_client.post("/api/v1/onboarding/exam-board", json={"exam_board": "edexcel"})
    await onboarding_client.post("/api/v1/onboarding/exam-date", json={"exam_date": "2027-05-01"})
    await onboarding_client.post("/api/v1/onboarding/target-grade", json={"target_grade": "A*"})
    r = await onboarding_client.post(
        "/api/v1/onboarding/preferences",
        json={"worked_examples": True, "visual": False, "step_by_step": True, "practice": False},
    )
    assert r.status_code == 200
    body = r.json()
    # After all steps including preferences, should be at roadmap (not yet onboarded_at)
    assert body["next_step"] == "roadmap"


@pytest.mark.asyncio
async def test_complete_finalizes_drafts(onboarding_client):
    """Full onboarding flow should finalize with done."""
    await onboarding_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    await onboarding_client.post("/api/v1/onboarding/exam-board", json={"exam_board": "edexcel"})
    await onboarding_client.post("/api/v1/onboarding/exam-date", json={"exam_date": "2027-05-01"})
    await onboarding_client.post("/api/v1/onboarding/target-grade", json={"target_grade": "A*"})
    await onboarding_client.post(
        "/api/v1/onboarding/preferences",
        json={"worked_examples": True, "visual": False, "step_by_step": True, "practice": False},
    )
    r = await onboarding_client.post("/api/v1/onboarding/complete")
    assert r.status_code == 200
    body = r.json()
    assert body["next_step"] == "done"
    assert body["progress_pct"] == 100


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(unauth_client):
    """Without auth token, wizard state should return 401."""
    r = await unauth_client.get("/api/v1/onboarding/state")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_post_subjects_rejects_unsupported(onboarding_client):
    """POST /api/v1/onboarding/subjects should reject unsupported subjects with 400."""
    r = await onboarding_client.post(
        "/api/v1/onboarding/subjects",
        json={"subjects": ["physics"]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_exam_board_rejects_unsupported(onboarding_client):
    """POST /api/v1/onboarding/exam-board should reject unsupported board combinations with 400."""
    # First set up a valid pure_mathematics subject
    await onboarding_client.post(
        "/api/v1/onboarding/subjects",
        json={"subjects": ["pure_mathematics"]},
    )
    # Try to set an unsupported exam board (aqa is not in SUPPORTED_COMBOS for any subject)
    r = await onboarding_client.post(
        "/api/v1/onboarding/exam-board",
        json={"exam_board": "aqa"},
    )
    assert r.status_code == 400
