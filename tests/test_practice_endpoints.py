import pytest
import json


@pytest.mark.asyncio
async def test_start_session_dispatches_quick_practice(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
        "topic": "integration_basics",
    })
    assert r.status_code == 201
    body = r.json()
    assert "session_id" in body


@pytest.mark.asyncio
async def test_quick_practice_requires_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
    })
    assert r.status_code == 400
    assert "topic required" in r.json()["detail"]


@pytest.mark.asyncio
async def test_drill_in_requires_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "drill_in",
    })
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_weak_areas_starts_without_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "weak_areas",
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_planner_reason_persisted_on_session_messages(authed_client, db_session, student_with_subject, syllabus_edexcel_seeded):
    from app.db.models import TutorSession
    from sqlalchemy import select

    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
        "topic": "integration_basics",
    })
    session_id = r.json()["session_id"]

    row = (await db_session.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )).scalar_one()
    system_entries = [
        m for m in row.messages
        if m.get("role") == "system" and m.get("content", "").startswith("planner_reason:")
    ]
    assert len(system_entries) == 1
    payload = json.loads(system_entries[0]["content"].removeprefix("planner_reason:"))
    assert payload["topic_selections"][0]["signal"] == "user_selected"


@pytest.mark.asyncio
async def test_practice_topics_fresh_student(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.get("/api/v1/practice/topics?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # Fresh student — all topics have no attempts, mastery = 0
    for t in body:
        assert t["has_attempts"] is False
        assert t["mastery_pct"] == 0
    # Ordering: syllabus ordinal
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    expected_first = EDEXCEL_9MA0_TOPICS[0]["topic_id"]
    assert body[0]["topic_id"] == expected_first


@pytest.mark.asyncio
async def test_practice_topics_returning_student_orders_attempted_first(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from app.db.models import MasteryState
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.30, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.10, total_attempts=2),
    ])
    await db_session.flush()

    r = await authed_client.get("/api/v1/practice/topics?subject=pure_mathematics")
    body = r.json()

    # Attempted topics first, weakest first
    assert body[0]["topic_id"] == "differentiation_basics"
    assert body[0]["has_attempts"] is True
    assert body[0]["mastery_pct"] == 10
    assert body[1]["topic_id"] == "integration_basics"
    assert body[1]["has_attempts"] is True
    assert body[1]["mastery_pct"] == 30
    # Remaining topics are unattempted syllabus topics
    assert body[2]["has_attempts"] is False


@pytest.mark.asyncio
async def test_practice_session_auto_closes_after_1h(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from datetime import datetime, timezone, timedelta
    from app.db.models import TutorSession
    from sqlalchemy import select

    stale = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="quick_practice",
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        ended_at=None,
    )
    db_session.add(stale)
    await db_session.flush()

    # Hit the dashboard — cleanup runs on load
    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert r.status_code == 200

    await db_session.refresh(stale)
    assert stale.ended_at is not None


@pytest.mark.asyncio
async def test_todays_focus_session_still_uses_24h_window(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from datetime import datetime, timezone, timedelta
    from app.db.models import TutorSession

    still_active = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="practice",   # Today's Focus
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        ended_at=None,
    )
    db_session.add(still_active)
    await db_session.flush()

    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert r.status_code == 200

    await db_session.refresh(still_active)
    # Still within 24h — should NOT be auto-closed
    assert still_active.ended_at is None


@pytest.mark.asyncio
async def test_practice_session_excluded_from_resume_card(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from app.db.models import TutorSession

    active_practice = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="quick_practice",
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        ended_at=None,
    )
    db_session.add(active_practice)
    await db_session.flush()

    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    body = r.json()
    assert body["resume_session"] is None
