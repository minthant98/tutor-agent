"""Tests for GET /api/v1/topics/v3/{topic_id} — topic detail v3 endpoint."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_topic_detail_v3_returns_five_section_shape(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Endpoint returns the five-section payload shape for a known topic."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
        )
    assert r.status_code == 200
    body = r.json()
    # Must have all five top-level sections
    assert "topic" in body
    assert "common_mistakes" in body
    assert "recent_attempts" in body
    assert "recommended_practice_href" in body
    assert "related_topics" in body

    # topic sub-fields
    topic = body["topic"]
    assert "id" in topic
    assert "label" in topic
    assert "mastery" in topic
    assert "syllabus_ref" in topic
    assert "target_grade" in topic

    # types
    assert isinstance(body["common_mistakes"], list)
    assert isinstance(body["recent_attempts"], list)
    assert isinstance(body["related_topics"], list)
    assert isinstance(body["recommended_practice_href"], str)


@pytest.mark.asyncio
async def test_topic_detail_v3_fresh_student_no_common_mistakes(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Fresh student → common_mistakes is empty list."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
        )
    assert r.status_code == 200
    body = r.json()
    assert body["common_mistakes"] == []


@pytest.mark.asyncio
async def test_topic_detail_v3_auth_required(
    unauth_client, student_with_subject, syllabus_edexcel_seeded
):
    """Endpoint requires authentication — 401 without token."""
    r = await unauth_client.get(
        "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_topic_detail_v3_unknown_topic_404(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """Unknown topic_id returns 404."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/this_topic_does_not_exist?subject=pure_mathematics"
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_topic_detail_v3_unknown_subject_404(
    authed_client, student_with_subject
):
    """Unknown subject returns 404."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=nonexistent_subject"
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_topic_detail_v3_common_mistakes_have_evidence(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """When common_mistakes are present, each item has non-empty evidence_submission_ids."""
    fake_mistakes = [
        {
            "text": "Across your last three attempts, limits of integration caused the lost marks.",
            "evidence_submission_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
        }
    ]
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=fake_mistakes),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
        )
    assert r.status_code == 200
    body = r.json()
    assert len(body["common_mistakes"]) == 1
    mistake = body["common_mistakes"][0]
    assert "text" in mistake
    assert "evidence_submission_ids" in mistake
    assert len(mistake["evidence_submission_ids"]) > 0


@pytest.mark.asyncio
async def test_topic_detail_v3_practice_href_format(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """recommended_practice_href links to drill_in mode for this topic."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
        )
    assert r.status_code == 200
    body = r.json()
    href = body["recommended_practice_href"]
    assert "drill_in" in href
    assert "algebra_indices_surds" in href


@pytest.mark.asyncio
async def test_topic_detail_v3_mastery_range(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    """mastery is an integer 0..100."""
    with patch(
        "app.api.v1.endpoints.topics.topic_mistakes.generate",
        new=AsyncMock(return_value=[]),
    ):
        r = await authed_client.get(
            "/api/v1/topics/v3/algebra_indices_surds?subject=pure_mathematics"
        )
    assert r.status_code == 200
    body = r.json()
    mastery = body["topic"]["mastery"]
    assert isinstance(mastery, int)
    assert 0 <= mastery <= 100
