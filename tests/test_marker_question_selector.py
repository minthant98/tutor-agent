import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.marker import question_selector as qs
from app.db.models import MasteryState, GradedUpload


@pytest.mark.asyncio
async def test_pick_question_uses_topic_override(db_session, student_with_subject, syllabus_edexcel_seeded):
    """When topic_override provided, skip weakness detection."""
    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x^2",
         "paper_ref": "Edexcel P1 2024", "topic": "integration_basics"}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS: x^3/3 + C", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["topic"] == "integration_basics"
    assert result["max_marks"] == 3
    assert result["used_generated_mark_scheme"] is False


@pytest.mark.asyncio
async def test_pick_question_weakness_driven_default(db_session, student_with_subject, syllabus_edexcel_seeded):
    """No topic_override → pick weakest topic with attempts."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.20, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.60, total_attempts=5),
    ])
    await db_session.flush()

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x^2",
         "paper_ref": "Edexcel P1 2024", "topic": "integration_basics"}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
        )
    assert result["topic"] == "integration_basics"  # weakest


@pytest.mark.asyncio
async def test_pick_question_fresh_student_fallback(db_session, student_with_subject, syllabus_edexcel_seeded):
    """No mastery → fall back to first syllabus topic in ordinal order."""
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_topic = EDEXCEL_9MA0_TOPICS[0]["topic_id"]

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "…",
         "paper_ref": "P1 2024", "topic": first_topic}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 4))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
        )
    assert result["topic"] == first_topic


@pytest.mark.asyncio
async def test_pick_question_history_avoidance(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Questions already in graded_uploads should be filtered out."""
    db_session.add(GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q_seen", question_text="Old",
        mark_scheme="Old MS", max_marks=3, input_type="typed",
        status="graded",
    ))
    await db_session.flush()

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q_seen", "question_text": "Old", "paper_ref": "P", "topic": "integration_basics"},
        {"question_id": "q_new",  "question_text": "New", "paper_ref": "P", "topic": "integration_basics"},
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["question_id"] == "q_new"


@pytest.mark.asyncio
async def test_extract_max_marks_regex_hits():
    assert qs._extract_max_marks_from_text("Total: 5 marks") == 5
    assert qs._extract_max_marks_from_text("[3 marks]") == 3
    assert qs._extract_max_marks_from_text("Some text [7 mark]") == 7


@pytest.mark.asyncio
async def test_extract_max_marks_fallback_default():
    """Regex fails + LLM extraction mocked to fail → default 5."""
    with patch.object(qs, "_extract_max_marks_via_llm", new=AsyncMock(side_effect=Exception("LLM down"))):
        result = await qs._extract_max_marks("no mark tokens here")
    assert result == 5


@pytest.mark.asyncio
async def test_no_mark_scheme_flag_set(db_session, student_with_subject, syllabus_edexcel_seeded):
    """If mark scheme retrieval returns None, generate one via LLM and flag the response."""
    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x", "paper_ref": "P", "topic": "integration_basics"},
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=None)), \
         patch.object(qs, "_generate_mark_scheme_llm",
                     new=AsyncMock(return_value=("Generated MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["used_generated_mark_scheme"] is True
    assert result["mark_scheme"] == "Generated MS"
