import logging
from typing import Any

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from app.core.config import settings
from app.rag.qdrant_ingestor import COLLECTION_NAME, get_qdrant_client



logger = logging.getLogger(__name__)

_client = None
_encoder = None
_reranker = None


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


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder reranker...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("Reranker loaded.")
    return _reranker


def preload_models():
    """Call this at startup to pre-load all models."""
    logger.info("Pre-loading embedding model...")
    _get_encoder()
    logger.info("Pre-loading reranker model...")
    _get_reranker()
    logger.info("All models loaded.")


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

        # Step 1 — retrieve top 20 candidates
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=20,
            with_payload=True,
        ).points

        if not results:
            return []

        # Step 2 — rerank
        reranker = _get_reranker()
        texts = [r.payload.get("text", "") for r in results]
        pairs = [[query, text] for text in texts]
        scores = reranker.predict(pairs)

        # Step 3 — sort and take top n
        ranked = sorted(
            zip(scores, results),
            key=lambda x: x[0],
            reverse=True,
        )[:n_results]

        chunks = []
        for score, result in ranked:
            payload = result.payload or {}
            chunks.append({
                "text": payload.get("text", ""),
                "source": payload.get("source_file", "unknown"),
                "score": round(float(score), 3),
                "metadata": payload,
            })

        logger.info("Retrieved %d reranked chunks for: %s", len(chunks), query[:50])
        return chunks

    except Exception as e:
        logger.warning("Qdrant retrieval failed: %s", e)
        return []