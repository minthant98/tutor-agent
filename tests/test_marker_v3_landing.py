"""Tests for GET /api/v1/marker/v3/landing and marker_narration service."""
import pytest
from unittest.mock import AsyncMock, patch


# ── narration service behavioural tests ──────────────────────────────────────

def test_marker_narration_system_instruction_no_praise():
    """SYSTEM_INSTRUCTION must forbid praise phrases."""
    from app.services.narration.marker_narration import SYSTEM_INSTRUCTION
    assert "NEVER praise" in SYSTEM_INSTRUCTION


def test_marker_narration_system_instruction_no_speculation():
    """SYSTEM_INSTRUCTION must forbid speculation."""
    from app.services.narration.marker_narration import SYSTEM_INSTRUCTION
    assert "NEVER speculate" in SYSTEM_INSTRUCTION


def test_marker_narration_system_instruction_requires_evidence():
    """SYSTEM_INSTRUCTION must require evidence/why clause."""
    from app.services.narration.marker_narration import SYSTEM_INSTRUCTION
    assert "ALWAYS explain WHY" in SYSTEM_INSTRUCTION


@pytest.mark.asyncio
async def test_marker_narration_generate_returns_string():
    """generate() must return a string given a context dict."""
    from app.services.narration import marker_narration
    with patch("app.services.narration.marker_narration.llm") as mock_llm:
        mock_llm.generate = AsyncMock(
            return_value="Integration accuracy averaged 62% across the last four submissions."
        )
        result = await marker_narration.generate({
            "recent_grade_pct": 62.0,
            "weak_topic": "integration",
            "week_submission_count": 4,
        })
    assert isinstance(result, str)
    assert len(result) > 0


# ── endpoint tests ────────────────────────────────────────────────────────────

_FAKE_CANDIDATE = {
    "question_id": "q_abc",
    "question_text": "Integrate x^2 from 0 to 1",
    "mark_scheme": "MS",
    "max_marks": 4,
    "paper_ref": "Edexcel 9MA0 · 2024 Q3",
    "topic": "integration",
    "used_generated_mark_scheme": False,
}

_FAKE_NARRATION = (
    "Integration accuracy averaged 62% across the last four submissions. "
    "Today's question targets substitution before partial fractions."
)


@pytest.mark.asyncio
async def test_v3_landing_returns_full_payload(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    with (
        patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=_FAKE_CANDIDATE)),
        patch("app.services.narration.marker_narration.llm") as mock_llm,
    ):
        mock_llm.generate = AsyncMock(return_value=_FAKE_NARRATION)
        r = await authed_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")

    assert r.status_code == 200
    body = r.json()
    assert "narration" in body
    assert "question" in body
    assert body["question"]["id"] == "q_abc"
    assert body["question"]["max_marks"] == 4
    assert "refresh_count_used" in body
    assert "refresh_limit" in body
    assert "tier" in body
    assert "recent_submissions" in body
    assert isinstance(body["recent_submissions"], list)


@pytest.mark.asyncio
async def test_v3_landing_requires_auth(
    unauth_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await unauth_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_v3_landing_refresh_count_matches_today_grades(
    authed_client, student_with_subject, db_session, syllabus_edexcel_seeded
):
    from app.db.models import GradedUpload
    # Seed 3 graded_uploads for today
    for i in range(3):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            exam_board="edexcel",
            question_id=f"q{i}",
            question_text="Integrate x^2",
            mark_scheme="MS",
            max_marks=4,
            input_type="typed",
            answer_text="A",
            status="graded",
        ))
    await db_session.flush()

    with (
        patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=_FAKE_CANDIDATE)),
        patch("app.services.narration.marker_narration.llm") as mock_llm,
    ):
        mock_llm.generate = AsyncMock(return_value=_FAKE_NARRATION)
        r = await authed_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")

    assert r.status_code == 200
    body = r.json()
    assert body["refresh_count_used"] == 3


@pytest.mark.asyncio
async def test_v3_landing_free_tier_has_refresh_limit(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    with (
        patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=_FAKE_CANDIDATE)),
        patch("app.services.narration.marker_narration.llm") as mock_llm,
    ):
        mock_llm.generate = AsyncMock(return_value=_FAKE_NARRATION)
        r = await authed_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")

    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "free"
    assert body["refresh_limit"] == 5


@pytest.mark.asyncio
async def test_v3_landing_pro_tier_has_null_refresh_limit(
    authed_client, student_with_subject, db_session, syllabus_edexcel_seeded
):
    from app.db.models import Student
    from sqlalchemy import update
    await db_session.execute(
        update(Student).where(Student.id == student_with_subject.id)
        .values(subscription_tier="pro")
    )
    await db_session.flush()

    with (
        patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=_FAKE_CANDIDATE)),
        patch("app.services.narration.marker_narration.llm") as mock_llm,
    ):
        mock_llm.generate = AsyncMock(return_value=_FAKE_NARRATION)
        r = await authed_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")

    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "pro"
    assert body["refresh_limit"] is None


@pytest.mark.asyncio
async def test_v3_landing_recent_submissions_max_5(
    authed_client, student_with_subject, db_session, syllabus_edexcel_seeded
):
    from app.db.models import GradedUpload
    for i in range(7):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id,
            subject="pure_mathematics",
            exam_board="edexcel",
            question_id=f"q{i}",
            question_text="Integrate x^2",
            mark_scheme="MS",
            max_marks=4,
            input_type="typed",
            answer_text="A",
            status="graded",
            marks_awarded=3,
        ))
    await db_session.flush()

    with (
        patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=_FAKE_CANDIDATE)),
        patch("app.services.narration.marker_narration.llm") as mock_llm,
    ):
        mock_llm.generate = AsyncMock(return_value=_FAKE_NARRATION)
        r = await authed_client.get("/api/v1/marker/v3/landing?subject=pure_mathematics")

    assert r.status_code == 200
    body = r.json()
    assert len(body["recent_submissions"]) <= 5
