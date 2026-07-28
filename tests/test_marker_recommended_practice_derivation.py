"""Tests for app.services.marker.recommended_practice.compute().

These tests run against the pure-Python logic — no DB connection needed
because compute() only reads from the GradedUpload object (no async queries).
We pass a mock object to avoid DB overhead.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


def _make_submission(
    subject: str = "pure_mathematics",
    feedback_json: dict | None = None,
) -> MagicMock:
    """Build a minimal GradedUpload-like mock."""
    upload = MagicMock()
    upload.subject = subject
    upload.feedback_json = feedback_json
    return upload


def _missed_criterion(code: str = "M1", description: str = "Use substitution") -> dict:
    return {"code": code, "description": description, "awarded": False, "comment": ""}


def _awarded_criterion(code: str = "A1", description: str = "Correct answer") -> dict:
    return {"code": code, "description": description, "awarded": True, "comment": ""}


# ---------------------------------------------------------------------------
# Test 1: graded submission with a missed criterion whose description contains
#         "substitution" → returns expected recommendation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommended_practice_targets_missed_criterion():
    """Missed M1 with 'substitution' in description → topic=integration_basics,
    sub_skill=substitution, blurb contains 'substitution'."""
    from app.services.marker import recommended_practice

    submission = _make_submission(
        feedback_json={
            "criteria": [
                _missed_criterion(code="M1", description="Use substitution to simplify the integral"),
                _awarded_criterion(code="A1", description="Correct answer"),
            ]
        }
    )

    result = await recommended_practice.compute(db=None, submission=submission)

    assert result is not None
    assert result["topic_id"] == "integration_basics"
    assert result["sub_skill"] == "substitution"
    assert "substitution" in result["blurb"].lower()


# ---------------------------------------------------------------------------
# Test 2: all criteria awarded → returns None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommended_practice_none_when_all_awarded():
    """When every criterion is awarded, compute() must return None."""
    from app.services.marker import recommended_practice

    submission = _make_submission(
        feedback_json={
            "criteria": [
                _awarded_criterion(code="M1", description="Set up integral correctly"),
                _awarded_criterion(code="A1", description="Correct answer"),
                _awarded_criterion(code="A2", description="Simplified correctly"),
            ]
        }
    )

    result = await recommended_practice.compute(db=None, submission=submission)

    assert result is None


# ---------------------------------------------------------------------------
# Test 3: missed criterion whose description does not match any keyword →
#         sub_skill falls back to topic_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommended_practice_fallback_to_topic_when_no_keyword_match():
    """Criterion description that doesn't hit any keyword → sub_skill == topic_id."""
    from app.services.marker import recommended_practice

    submission = _make_submission(
        feedback_json={
            "criteria": [
                _missed_criterion(
                    code="M1",
                    description="Show all working clearly",  # no keyword match
                ),
            ]
        }
    )

    result = await recommended_practice.compute(db=None, submission=submission)

    assert result is not None
    # sub_skill must equal topic_id when no keyword matched
    assert result["sub_skill"] == result["topic_id"]
    # blurb should still be meaningful
    assert len(result["blurb"]) > 0
