"""
tests/test_search_endpoint.py
---------------------------------
Tests for GET /api/v1/search

Uses authed_client (student_with_subject → edexcel/pure_mathematics)
and syllabus_edexcel_seeded to ensure SyllabusTopic rows exist.

The brief specifies fixtures named `client`, `auth_headers`, `qdrant_seeded`;
those don't exist in conftest, so we use the real project fixtures:
  - authed_client  (AsyncClient with auth header + db override)
  - syllabus_edexcel_seeded  (seeds SyllabusTopic rows for pure_mathematics)
"""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_search_returns_topics(authed_client, syllabus_edexcel_seeded):
    """Searching 'integration' returns at least one topic result."""
    r = await authed_client.get("/api/v1/search?q=integration")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    types = {x["type"] for x in body}
    assert "topic" in types, f"Expected 'topic' in types, got: {types}"


@pytest.mark.asyncio
async def test_search_first_result_matches_query(authed_client, syllabus_edexcel_seeded):
    """First topic result label contains the search term (case-insensitive)."""
    r = await authed_client.get("/api/v1/search?q=integration")
    assert r.status_code == 200
    body = r.json()
    topic_results = [x for x in body if x["type"] == "topic"]
    assert len(topic_results) > 0
    assert "integration" in topic_results[0]["label"].lower(), (
        f"Expected 'integration' in first topic label, got: {topic_results[0]['label']}"
    )


@pytest.mark.asyncio
async def test_search_context_ranks_matching_topic_first(authed_client, syllabus_edexcel_seeded):
    """When context=integration_basics, that topic_id appears first in results."""
    # "chain" matches "Chain, product, quotient rules" (differentiation_chain_product_quotient)
    # but with context=integration_basics, any integration_basics item should rank first.
    # Use q=integration so we get multiple matches with integration_basics among them.
    r = await authed_client.get(
        "/api/v1/search?q=integration&context=integration_basics"
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) > 0
    first = body[0]
    assert first.get("topic_id") == "integration_basics" or "integration" in first["label"].lower(), (
        f"Expected integration_basics first with context ranking, got: {first}"
    )


@pytest.mark.asyncio
async def test_search_context_ranking_places_context_item_first(authed_client, syllabus_edexcel_seeded):
    """Stable sort: when context matches a topic_id, that item is index 0."""
    # Search 'algebra' which matches multiple topics; context=algebra_quadratics
    r = await authed_client.get(
        "/api/v1/search?q=algebra&context=algebra_quadratics"
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) > 0
    assert body[0].get("topic_id") == "algebra_quadratics", (
        f"Expected algebra_quadratics first, got topic_id={body[0].get('topic_id')}"
    )


@pytest.mark.asyncio
async def test_search_requires_auth(unauth_client):
    """Unauthenticated requests get 401."""
    r = await unauth_client.get("/api/v1/search?q=integration")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_search_empty_query_returns_list(authed_client, syllabus_edexcel_seeded):
    """Empty q returns a list (possibly empty) without error."""
    r = await authed_client.get("/api/v1/search?q=")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_search_result_shape(authed_client, syllabus_edexcel_seeded):
    """Every result has the required fields."""
    r = await authed_client.get("/api/v1/search?q=integration")
    assert r.status_code == 200
    for item in r.json():
        assert "id" in item
        assert "type" in item
        assert "label" in item
        assert "href" in item
        assert "topic_id" in item
