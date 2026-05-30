"""
app/core/session_store.py
--------------------------
Redis-backed persistence for SessionState.

Key schema : "session:{session_id}"
TTL        : SESSION_TTL_SECONDS (default 24h), refreshed on every write
"""

import json
import logging
import os
from typing import Optional

from app.core.redis_client import get_redis
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", 86400))
_KEY_PREFIX = "session:"


def _key(session_id: str) -> str:
    return f"{_KEY_PREFIX}{session_id}"


def save_session(state: SessionState) -> None:
    session_id = state["session_id"]
    try:
        r = get_redis()
        r.setex(_key(session_id), SESSION_TTL_SECONDS, json.dumps(dict(state), ensure_ascii=False, default=str))
    except Exception as exc:
        logger.exception("Failed to save session %s", session_id)
        raise RuntimeError(f"Session save failed: {exc}") from exc


def load_session(session_id: str) -> Optional[SessionState]:
    try:
        r = get_redis()
        data = r.get(_key(session_id))
    except Exception:
        logger.exception("Failed to load session %s", session_id)
        return None

    if data is None:
        return None

    try:
        return json.loads(data)  # type: ignore[return-value]
    except Exception:
        logger.exception("Failed to deserialize session %s", session_id)
        return None


def delete_session(session_id: str) -> Optional[SessionState]:
    r = get_redis()
    try:
        data = r.getdel(_key(session_id))
    except Exception:
        try:
            pipe = r.pipeline()
            pipe.get(_key(session_id))
            pipe.delete(_key(session_id))
            results = pipe.execute()
            data = results[0]
        except Exception:
            logger.exception("Failed to delete session %s", session_id)
            return None

    if data is None:
        return None

    try:
        return json.loads(data)  # type: ignore[return-value]
    except Exception:
        logger.exception("Failed to deserialize session %s on delete", session_id)
        return None
