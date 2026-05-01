import logging
from typing import Any

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.rag.qdrant_ingestor import COLLECTION_NAME, get_qdrant_client

logger = logging.getLogger(__name__)

_client = None
_encoder = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = get_qdrant_client()
    return _client


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


async def retrieve(
    query: str,
    subject: str,
    exam_board: str = "edexcel",
    exam_level: str = "a_level",
    n_results: int = 5,
) -> list[dict[str, Any]]:
    try:
        client = _get_client()
        encoder = _get_encoder()

        query_vector = encoder.encode(query).tolist()

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=n_results,
            with_payload=True,
        ).points

        chunks = []
        for result in results:
            score = result.score
            if score > 0.3:
                payload = result.payload or {}
                chunks.append({
                    "text": payload.get("text", ""),
                    "source": payload.get("source_file", "unknown"),
                    "score": round(score, 3),
                    "metadata": payload,
                })

        logger.info("Retrieved %d chunks for: %s", len(chunks), query[:50])
        return chunks

    except Exception as e:
        logger.warning("Qdrant retrieval failed: %s", e)
        return []