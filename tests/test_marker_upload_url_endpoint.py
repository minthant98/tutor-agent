"""Tests for POST /api/v1/marker/submissions/upload-url."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_upload_url_returns_signed_supabase_url(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    fake_url = "https://xxxx.supabase.co/storage/v1/object/upload/sign/graded_uploads/uploads/uuid/file.jpg?token=abc"
    with patch(
        "app.api.v1.endpoints.marker.generate_signed_upload_url",
        new=AsyncMock(return_value=fake_url),
    ):
        r = await authed_client.post(
            "/api/v1/marker/submissions/upload-url",
            json={"content_type": "image/jpeg", "filename": "page1.jpg"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["signed_url"].startswith("https://")
    assert "graded_uploads" in body["signed_url"]
    assert body["photo_path"].startswith("uploads/")


@pytest.mark.asyncio
async def test_upload_url_requires_auth(unauth_client):
    r = await unauth_client.post(
        "/api/v1/marker/submissions/upload-url",
        json={"content_type": "image/jpeg", "filename": "page1.jpg"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_upload_url_rejects_invalid_content_type(
    authed_client, student_with_subject
):
    r = await authed_client.post(
        "/api/v1/marker/submissions/upload-url",
        json={"content_type": "application/pdf", "filename": "doc.pdf"},
    )
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_upload_url_path_includes_student_id(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    fake_url = "https://xxxx.supabase.co/storage/v1/object/upload/sign/graded_uploads/uploads/uuid/file.png?token=xyz"
    with patch(
        "app.api.v1.endpoints.marker.generate_signed_upload_url",
        new=AsyncMock(return_value=fake_url),
    ):
        r = await authed_client.post(
            "/api/v1/marker/submissions/upload-url",
            json={"content_type": "image/png", "filename": "scan.png"},
        )
    assert r.status_code == 200
    body = r.json()
    # Path should be uploads/<student_id>/<uuid>.png
    assert body["photo_path"].endswith(".png")
    assert str(student_with_subject.id) in body["photo_path"]
