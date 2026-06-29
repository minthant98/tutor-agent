# app/core/feature_flags.py
import asyncio
import logging
import time
from typing import Iterable

logger = logging.getLogger(__name__)

FLAGS: Iterable[str] = (
    "dashboard_v2",
    "onboarding_v2",
    "session_engine_v2",
    "notifications_v2",
    "account_v2",
)

_CACHE: dict[tuple[str, str], tuple[bool, float]] = {}
_CACHE_TTL_SEC = 60


def _posthog_check(student_id: str, flag: str) -> bool:
    """Synchronous PostHog call, isolated so tests can patch it."""
    import posthog
    return bool(posthog.feature_enabled(flag, str(student_id)))


async def is_enabled(student_id, flag: str, default: bool = True) -> bool:
    if flag not in FLAGS:
        return default
    key = (str(student_id), flag)
    now = time.time()
    cached = _CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]
    try:
        result = await asyncio.to_thread(_posthog_check, str(student_id), flag)
    except Exception as exc:
        logger.warning("PostHog feature_enabled failed for %s/%s: %s", student_id, flag, exc)
        return default
    _CACHE[key] = (result, now + _CACHE_TTL_SEC)
    return result
