"""
app/core/session_store.py
--------------------------
Redis-backed persistence for SessionState.

Design notes
------------
* All fields are plain Python primitives (str, int, float, list, dict, None)
  EXCEPT image_bytes which is bytes | None.
* We handle image_bytes by base64-encoding it into the JSON payload so the
  entire state round-trips through a single json.dumps / json.loads call.
* Key schema  : "session:{session_id}"
* TTL         : SESSION_TTL_SECONDS (default 24 h). Refreshed on every write
                so active sessions never expire mid-conversation.
* All public functions are synchronous because redis-py's standard client
  releases the GIL during I/O and FastAPI runs sync code in a thread pool —
  no need for aioredis complexity.
"""

import base64
import json
import logging
import os
from typing import Optional

from app.core.redis_client import get_redis
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)

# How long a session lives in Redis after the last write.
SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", 86400))  # 24 h

_KEY_PREFIX = "session:"


def _make_key(session_id: str) -> str:
    return f"{_KEY_PREFIX}{session_id}"


# ── Serialization ─────────────────────────────────────────────────────────────

def _serialize(state: SessionState) -> bytes:
    """
    Convert SessionState → UTF-8 JSON bytes.

    image_bytes (bytes | None) is base64-encoded under the key
    "__image_bytes_b64__" so it survives a JSON round-trip.
    """
    payload: dict = dict(state)  # shallow copy; all values are already plain types

    raw_bytes = payload.pop("image_bytes", None)
    if raw_bytes is not None:
        payload["__image_bytes_b64__"] = base64.b64encode(raw_bytes).decode("ascii")
    else:
        payload["__image_bytes_b64__"] = None

    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _deserialize(data: bytes) -> SessionState:
    """
    Convert UTF-8 JSON bytes → SessionState.

    Restores image_bytes from the base64 sentinel key.
    """
    payload: dict = json.loads(data.decode("utf-8"))

    b64 = payload.pop("__image_bytes_b64__", None)
    payload["image_bytes"] = base64.b64decode(b64) if b64 is not None else None

    return SessionState(**payload)  # type: ignore[arg-type]


# ── Public API ────────────────────────────────────────────────────────────────

def save_session(state: SessionState) -> None:
    """
    Persist state to Redis and (re)set the TTL.
    Raises RuntimeError if the write fails so callers get a clear error
    rather than a silent data-loss bug.
    """
    session_id = state["session_id"]
    key = _make_key(session_id)
    try:
        r = get_redis()
        r.setex(key, SESSION_TTL_SECONDS, _serialize(state))
    except Exception as exc:
        logger.exception("Failed to save session %s to Redis", session_id)
        raise RuntimeError(f"Session save failed: {exc}") from exc


def load_session(session_id: str) -> Optional[SessionState]:
    """
    Load state from Redis.
    Returns None if the session doesn't exist or has expired.
    """
    key = _make_key(session_id)
    try:
        r = get_redis()
        data = r.get(key)
    except Exception:
        logger.exception("Failed to load session %s from Redis", session_id)
        return None

    if data is None:
        return None

    try:
        return _deserialize(data)
    except Exception:
        logger.exception("Failed to deserialize session %s", session_id)
        return None


def delete_session(session_id: str) -> Optional[SessionState]:
    """
    Atomically fetch-and-delete a session from Redis.
    Returns the final state (for end_session summary), or None if not found.

    Uses GETDEL (Redis 6.2+). Falls back to GET + DEL pipeline for older Redis.
    """
    key = _make_key(session_id)
    r = get_redis()

    try:
        # GETDEL is atomic — preferred
        data = r.getdel(key)
    except Exception:
        # Fallback: pipeline GET + DEL (still fast, not perfectly atomic but fine here)
        try:
            pipe = r.pipeline()
            pipe.get(key)
            pipe.delete(key)
            results = pipe.execute()
            data = results[0]
        except Exception:
            logger.exception("Failed to delete session %s from Redis", session_id)
            return None

    if data is None:
        return None

    try:
        return _deserialize(data)
    except Exception:
        logger.exception("Failed to deserialize session %s on delete", session_id)
        return None