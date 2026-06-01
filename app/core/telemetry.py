"""
PostHog telemetry — server-side event capture.

All calls are non-blocking and silently no-op if POSTHOG_KEY is not set,
so the rest of the app never has to check whether telemetry is enabled.
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.posthog_key:
        return None
    try:
        from posthog import Posthog
        _client = Posthog(
            project_api_key=settings.posthog_key,
            host=settings.posthog_host,
        )
        logger.info("PostHog telemetry enabled (host=%s)", settings.posthog_host)
    except Exception as e:
        logger.warning("PostHog init failed: %s", e)
        _client = None
    return _client


def capture(distinct_id: str, event: str, properties: dict[str, Any] | None = None) -> None:
    """Fire-and-forget event capture. Never raises."""
    client = _get_client()
    if not client or not distinct_id:
        return
    try:
        client.capture(distinct_id=distinct_id, event=event, properties=properties or {})
    except Exception as e:
        logger.debug("PostHog capture failed (%s): %s", event, e)
