"""Tests for account endpoints (Task 17)."""
import pytest


@pytest.mark.asyncio
async def test_get_account_returns_profile(authed_client, student_with_subject):
    r = await authed_client.get("/api/v1/account")
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["name"]
    assert len(body["subjects"]) == 1


@pytest.mark.asyncio
async def test_get_account_structure(authed_client, student_with_subject):
    r = await authed_client.get("/api/v1/account")
    assert r.status_code == 200
    body = r.json()
    assert "profile" in body
    assert "subjects" in body
    assert "preferences" in body
    assert "billing" in body
    assert "email" in body["profile"]
    assert body["billing"]["tier"] == "free"


@pytest.mark.asyncio
async def test_patch_subject_updates_exam_date(authed_client, student_with_subject):
    sid = str(student_with_subject.subjects[0].id) if hasattr(student_with_subject, "subjects") and student_with_subject.subjects else None
    # Get subject id from /account
    r = await authed_client.get("/api/v1/account")
    assert r.status_code == 200
    subjects = r.json()["subjects"]
    assert len(subjects) == 1
    sid = subjects[0]["id"]
    r = await authed_client.patch(
        f"/api/v1/account/subjects/{sid}",
        json={"exam_date": "2027-06-01"},
    )
    assert r.status_code == 200
    assert r.json()["exam_date"] == "2027-06-01"


@pytest.mark.asyncio
async def test_patch_preferences(authed_client, student_with_subject):
    r = await authed_client.patch(
        "/api/v1/account/preferences",
        json={"worked_examples": True, "visual": False, "step_by_step": True, "practice": False},
    )
    assert r.status_code == 200
    assert r.json()["preferences"]["worked_examples"] is True


@pytest.mark.asyncio
async def test_patch_profile_name(authed_client, student_with_subject):
    r = await authed_client.patch("/api/v1/account/profile", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_get_account_requires_auth(unauth_client):
    r = await unauth_client.get("/api/v1/account")
    assert r.status_code == 401
