from datetime import datetime, timezone
from fastapi import Depends, HTTPException

from app.api.v1.endpoints.auth import get_current_student
from app.core.config import settings
from app.db.models import Student


def _end_of_day_unix() -> int:
    """UTC timestamp for 23:59:59 today."""
    now = datetime.now(timezone.utc)
    eod = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return int(eod.timestamp())


async def check_message_limit(student: Student = Depends(get_current_student)) -> Student:
    """
    Dependency for message endpoints.
    Pro students with active subscriptions pass through immediately.
    Free students are capped at settings.free_daily_message_limit per UTC day.
    Raises HTTP 429 with upgrade URL when the limit is reached.
    """
    if student.subscription_tier == "pro" and student.subscription_status == "active":
        return student

    from app.core.redis_client import get_redis
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"rate:{student.id}:{today}"

    r = get_redis()
    raw = r.get(key)
    current = int(raw) if raw else 0

    if current >= settings.free_daily_message_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "rate_limit_exceeded",
                "message": (
                    f"Free plan allows {settings.free_daily_message_limit} messages per day. "
                    "Upgrade to Pro for unlimited access."
                ),
                "upgrade_url": f"{settings.frontend_url}/pricing",
            },
        )

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expireat(key, _end_of_day_unix())
    pipe.execute()

    return student
