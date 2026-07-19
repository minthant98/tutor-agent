"""Tests for app/services/narration/topic_mistakes.py."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.services.narration import topic_mistakes as tm


# ── SYSTEM_INSTRUCTION content assertions ────────────────────────────────────

def test_system_instruction_bans_praise():
    """SYSTEM_INSTRUCTION must explicitly list banned praise phrases."""
    s = tm.SYSTEM_INSTRUCTION.lower()
    for banned in ["great job", "well done", "amazing", "keep it up", "good attempt"]:
        assert banned in s, f"SYSTEM_INSTRUCTION must ban '{banned}'"


def test_system_instruction_forbids_invention():
    """SYSTEM_INSTRUCTION must ban inventing facts not in the evidence."""
    s = tm.SYSTEM_INSTRUCTION.lower()
    assert "never invent" in s or "do not invent" in s or "invent" in s


def test_system_instruction_requires_evidence():
    """SYSTEM_INSTRUCTION must require evidence_submission_ids to be non-empty."""
    s = tm.SYSTEM_INSTRUCTION.lower()
    assert "evidence_submission_ids" in s or "evidence" in s


def test_system_instruction_caps_at_three():
    """SYSTEM_INSTRUCTION must limit output to at most 3 items."""
    s = tm.SYSTEM_INSTRUCTION.lower()
    assert "3" in s or "three" in s


# ── Fresh student (no attempts) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_common_mistakes_empty_when_no_attempts(db_session, student):
    """Fresh student with no GradedUpload rows → returns [] without calling LLM."""
    with patch.object(tm.llm, "generate", new=AsyncMock(return_value="[]")) as mock_llm:
        result = await tm.generate(db_session, student.id, "integration_basics")
    assert result == []
    # LLM must NOT be called for fresh student
    mock_llm.assert_not_called()


# ── Evidence requirement ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_common_mistakes_all_have_evidence(db_session, student):
    """Every returned item must have non-empty evidence_submission_ids."""
    from app.db.models import GradedUpload
    import json

    # Seed 3 graded uploads for the student
    sub_ids = []
    for i in range(3):
        sub_id = uuid.uuid4()
        sub_ids.append(str(sub_id))
        upload = GradedUpload(
            id=sub_id,
            student_id=student.id,
            subject="pure_mathematics",
            exam_board="edexcel",
            question_id=f"q_{i}",
            question_text=f"Integrate x^{i} from 0 to 1",
            mark_scheme=f"Mark scheme {i}",
            max_marks=6,
            input_type="typed",
            answer_text="Student answer here",
            marks_awarded=4,
            grade_pct=0.67,
            feedback_json={
                "missed_criteria": ["Did not state limits correctly", "Forgot constant of integration"],
                "improvement": "Check limits of integration carefully",
                "criteria_feedback": ["Substitution was correct but limits wrong"],
            },
            status="graded",
        )
        db_session.add(upload)
    await db_session.flush()

    # Mock LLM to return a valid response referencing real submission IDs
    llm_response = json.dumps([
        {
            "text": "Across your last three attempts, limits of integration caused the lost marks.",
            "evidence_submission_ids": sub_ids[:2],
        }
    ])

    with patch.object(tm.llm, "generate", new=AsyncMock(return_value=llm_response)):
        result = await tm.generate(db_session, student.id, "integration_basics", subject="pure_mathematics")

    assert len(result) <= 3
    for m in result:
        assert m["evidence_submission_ids"], "Each mistake must have non-empty evidence_submission_ids"
        assert m["text"], "Each mistake must have non-empty text"


@pytest.mark.asyncio
async def test_common_mistakes_drops_items_without_evidence(db_session, student):
    """Items returned by LLM with empty evidence_submission_ids are dropped."""
    from app.db.models import GradedUpload
    import json

    sub_id = uuid.uuid4()
    upload = GradedUpload(
        id=sub_id,
        student_id=student.id,
        subject="pure_mathematics",
        exam_board="edexcel",
        question_id="q_1",
        question_text="Differentiate x^2",
        mark_scheme="2x",
        max_marks=4,
        input_type="typed",
        answer_text="Student answer",
        marks_awarded=2,
        grade_pct=0.5,
        feedback_json={"missed_criteria": ["Chain rule not applied"]},
        status="graded",
    )
    db_session.add(upload)
    await db_session.flush()

    # LLM returns one valid item + one item with empty evidence → only valid one survives
    llm_response = json.dumps([
        {
            "text": "Valid mistake with evidence.",
            "evidence_submission_ids": [str(sub_id)],
        },
        {
            "text": "Hallucinated mistake with no evidence.",
            "evidence_submission_ids": [],
        },
    ])

    with patch.object(tm.llm, "generate", new=AsyncMock(return_value=llm_response)):
        result = await tm.generate(db_session, student.id, "differentiation_basics", subject="pure_mathematics")

    assert len(result) == 1
    assert result[0]["text"] == "Valid mistake with evidence."
    assert result[0]["evidence_submission_ids"] == [str(sub_id)]


@pytest.mark.asyncio
async def test_common_mistakes_drops_hallucinated_ids(db_session, student):
    """Items referencing submission IDs not in the evidence set are dropped."""
    from app.db.models import GradedUpload
    import json

    real_id = uuid.uuid4()
    upload = GradedUpload(
        id=real_id,
        student_id=student.id,
        subject="pure_mathematics",
        exam_board="edexcel",
        question_id="q_real",
        question_text="Integrate x^2",
        mark_scheme="x^3/3 + C",
        max_marks=4,
        input_type="typed",
        answer_text="x^3/3",
        marks_awarded=3,
        grade_pct=0.75,
        feedback_json={"missed_criteria": ["Forgot constant of integration"]},
        status="graded",
    )
    db_session.add(upload)
    await db_session.flush()

    fake_id = str(uuid.uuid4())  # Does not exist in DB
    llm_response = json.dumps([
        {
            "text": "Hallucinated mistake with fake submission ID.",
            "evidence_submission_ids": [fake_id],
        },
    ])

    with patch.object(tm.llm, "generate", new=AsyncMock(return_value=llm_response)):
        result = await tm.generate(db_session, student.id, "integration_basics", subject="pure_mathematics")

    # The item with a fake/hallucinated ID must be dropped
    assert result == []


@pytest.mark.asyncio
async def test_common_mistakes_caps_at_three(db_session, student):
    """LLM returning more than 3 items must be capped to 3."""
    from app.db.models import GradedUpload
    import json

    sub_ids = []
    for i in range(5):
        sub_id = uuid.uuid4()
        sub_ids.append(str(sub_id))
        upload = GradedUpload(
            id=sub_id,
            student_id=student.id,
            subject="pure_mathematics",
            exam_board="edexcel",
            question_id=f"q_{i}",
            question_text=f"Question {i}",
            mark_scheme=f"Scheme {i}",
            max_marks=6,
            input_type="typed",
            answer_text="answer",
            marks_awarded=3,
            grade_pct=0.5,
            feedback_json={"missed_criteria": [f"Error {i}"]},
            status="graded",
        )
        db_session.add(upload)
    await db_session.flush()

    # LLM returns 5 items
    llm_response = json.dumps([
        {"text": f"Mistake {i}.", "evidence_submission_ids": [sub_ids[i]]}
        for i in range(5)
    ])

    with patch.object(tm.llm, "generate", new=AsyncMock(return_value=llm_response)):
        result = await tm.generate(db_session, student.id, "integration_basics", subject="pure_mathematics")

    assert len(result) <= 3


@pytest.mark.asyncio
async def test_generate_passes_system_instruction_to_llm(db_session, student):
    """generate() must invoke llm.generate with SYSTEM_INSTRUCTION when attempts exist."""
    from app.db.models import GradedUpload
    import json

    sub_id = uuid.uuid4()
    upload = GradedUpload(
        id=sub_id,
        student_id=student.id,
        subject="pure_mathematics",
        exam_board="edexcel",
        question_id="q_test",
        question_text="Test question",
        mark_scheme="Test scheme",
        max_marks=4,
        input_type="typed",
        answer_text="test",
        marks_awarded=2,
        grade_pct=0.5,
        feedback_json={"improvement": "Work on this"},
        status="graded",
    )
    db_session.add(upload)
    await db_session.flush()

    with patch.object(tm.llm, "generate", new=AsyncMock(return_value="[]")) as mock_llm:
        await tm.generate(db_session, student.id, "integration_basics", subject="pure_mathematics")

    mock_llm.assert_called_once()
    call_kwargs = mock_llm.call_args.kwargs
    assert call_kwargs.get("system") == tm.SYSTEM_INSTRUCTION, "SYSTEM_INSTRUCTION must be passed to LLM"
