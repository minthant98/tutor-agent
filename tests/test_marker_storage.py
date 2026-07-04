import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.marker import storage


def test_build_photo_path_jpg():
    sid = uuid4()
    subid = uuid4()
    path = storage.build_photo_path(sid, subid, "jpg")
    assert path == f"{sid}/{subid}.jpg"


def test_build_photo_path_rejects_unknown_ext():
    with pytest.raises(ValueError):
        storage.build_photo_path(uuid4(), uuid4(), "gif")


@pytest.mark.asyncio
async def test_generate_signed_upload_url():
    fake_client = MagicMock()
    fake_client.storage.from_.return_value.create_signed_upload_url.return_value = {
        "signed_url": "https://supabase.example/upload?token=abc",
        "path": "path.jpg",
        "token": "abc",
    }
    with patch.object(storage, "_get_client", return_value=fake_client):
        url = await storage.generate_signed_upload_url("student1/sub1.jpg", "image/jpeg")
    assert url.startswith("https://supabase.example/upload")


@pytest.mark.asyncio
async def test_generate_signed_download_url():
    fake_client = MagicMock()
    fake_client.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://supabase.example/download?token=xyz"
    }
    with patch.object(storage, "_get_client", return_value=fake_client):
        url = await storage.generate_signed_download_url("student1/sub1.jpg")
    assert "download" in url


@pytest.mark.asyncio
async def test_check_bucket_exists_success():
    fake_client = MagicMock()
    fake_client.storage.get_bucket.return_value = {"name": "graded_uploads"}
    with patch.object(storage, "_get_client", return_value=fake_client):
        assert await storage.check_bucket_exists() is True


@pytest.mark.asyncio
async def test_check_bucket_exists_failure():
    fake_client = MagicMock()
    fake_client.storage.get_bucket.side_effect = Exception("bucket not found")
    with patch.object(storage, "_get_client", return_value=fake_client):
        assert await storage.check_bucket_exists() is False
