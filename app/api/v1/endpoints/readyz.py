# app/api/v1/endpoints/readyz.py
"""
GET /readyz — top-level readiness probe (mounted WITHOUT api_v1 prefix).

Checks:
1. DB connection + syllabus seed (SyllabusTopic rows for version 2026.1)
2. Redis connectivity
3. GROQ_API_KEY environment variable present
"""
import asyncio
import os

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.db.database import AsyncSessionLocal
from app.db.models import SyllabusTopic
from app.core.redis_client import get_redis

router = APIRouter(tags=["health"])

_SYLLABUS_VERSION = "2026.1"


@router.get("/readyz")
async def readyz() -> dict:
    failures: list[str] = []

    # 1. DB — check we can connect AND syllabus topics are seeded
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(func.count(SyllabusTopic.id)).where(
                    SyllabusTopic.version == _SYLLABUS_VERSION
                )
            )
            count = res.scalar() or 0
            if count == 0:
                failures.append("no_syllabus_topics")
    except Exception as e:
        failures.append(f"db: {e}")

    # 2. Redis — get_redis() is synchronous; run ping in thread to avoid blocking
    try:
        redis_client = get_redis()
        await asyncio.to_thread(redis_client.ping)
    except Exception as e:
        failures.append(f"redis: {e}")

    # 3. LLM key
    if not os.environ.get("GROQ_API_KEY"):
        failures.append("groq_api_key_missing")

    if failures:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "failures": failures},
        )

    return {"status": "ready"}
