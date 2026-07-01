"""Tests for today_focus_service cache layer: get_or_generate + invalidate_today."""
import json
import pytest
from app.services import today_focus_service as svc


@pytest.mark.asyncio
async def test_first_call_generates_and_caches(db_session, redis_client, student, syllabus_edexcel_seeded):
    out = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    assert out["generator_version"] == svc.GENERATOR_VERSION
    cached = redis_client.get(svc._cache_key(student.id, "pure_mathematics", out["focus_date"]))
    assert cached is not None


@pytest.mark.asyncio
async def test_second_call_reads_cache(db_session, redis_client, student, syllabus_edexcel_seeded):
    a = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    b = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    assert a["segment_plan"] == b["segment_plan"]  # exact same plan


@pytest.mark.asyncio
async def test_invalidate_clears_cache(db_session, redis_client, student, syllabus_edexcel_seeded):
    await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    svc.invalidate_today(redis_client, student.id, "pure_mathematics")
    # Cache should be gone now
    from datetime import date
    key = svc._cache_key(student.id, "pure_mathematics", date.today())
    assert redis_client.get(key) is None


@pytest.mark.asyncio
async def test_payload_has_required_fields(db_session, redis_client, student, syllabus_edexcel_seeded):
    out = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    required = {"shape", "segment_plan", "reasoning", "generator_version", "generated_at", "expires_at", "focus_date"}
    assert required.issubset(set(out.keys()))


@pytest.mark.asyncio
async def test_cache_key_format(student):
    from datetime import date
    today = date.today()
    key = svc._cache_key(student.id, "pure_mathematics", today)
    assert key == f"today_focus:{student.id}:pure_mathematics:{today.isoformat()}"


@pytest.mark.asyncio
async def test_persists_to_today_focus_history(db_session, redis_client, student, syllabus_edexcel_seeded):
    from sqlalchemy import select
    from app.db.models import TodayFocusHistory
    await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    row = (await db_session.execute(
        select(TodayFocusHistory).where(
            TodayFocusHistory.student_id == student.id,
            TodayFocusHistory.subject == "pure_mathematics",
        )
    )).scalar_one_or_none()
    assert row is not None
    assert row.generator_version == svc.GENERATOR_VERSION
    assert row.shape is not None
    assert len(row.segment_plan) == 3
