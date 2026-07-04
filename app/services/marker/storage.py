"""Supabase Storage helpers for the graded_uploads bucket.

Backend never proxies photo bytes — signed PUT URLs allow the client to upload
directly to Supabase. Signed GET URLs (short TTL) render photos in history.
"""
import asyncio
import logging
import os
from functools import lru_cache
from uuid import UUID

from supabase import Client, create_client

logger = logging.getLogger(__name__)

BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "graded_uploads")
UPLOAD_TTL_SEC = 300     # 5 minutes
DOWNLOAD_TTL_SEC = 900   # 15 minutes

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


@lru_cache(maxsize=1)
def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def build_photo_path(student_id: UUID, submission_id: UUID, ext: str) -> str:
    """Build the Supabase Storage object path for a submission photo."""
    ext_lower = ext.lower().lstrip(".")
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported extension: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    return f"{student_id}/{submission_id}.{ext_lower}"


async def generate_signed_upload_url(path: str, content_type: str) -> str:
    """Signed PUT URL for client-side upload. TTL 5 min."""
    def _sync():
        client = _get_client()
        result = client.storage.from_(BUCKET).create_signed_upload_url(path)
        return result["signed_url"] if "signed_url" in result else result["signedUrl"]
    return await asyncio.to_thread(_sync)


async def generate_signed_download_url(path: str) -> str:
    """Signed GET URL for viewing past photos. TTL 15 min."""
    def _sync():
        client = _get_client()
        result = client.storage.from_(BUCKET).create_signed_url(path, DOWNLOAD_TTL_SEC)
        return result["signedURL"] if "signedURL" in result else result["signed_url"]
    return await asyncio.to_thread(_sync)


async def check_bucket_exists() -> bool:
    """Health-check helper for /readyz. Returns False on any error (no raise)."""
    def _sync():
        client = _get_client()
        try:
            client.storage.get_bucket(BUCKET)
            return True
        except Exception as exc:
            logger.warning("Supabase bucket check failed: %s", exc)
            return False
    return await asyncio.to_thread(_sync)
