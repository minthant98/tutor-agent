import logging
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.rag.ingestor import collection_name, get_chroma_client

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = get_chroma_client()
    return _client


async def retrieve(
    query: str,
    subject: str,
    exam_board: str = "cambridge",
    exam_level: str = "a_level",
    n_results: int = 5,
) -> list[dict[str, Any]]:
    try:
        client = _get_client()
        name = collection_name(subject, exam_board, exam_level)

        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name=name, embedding_function=ef)

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = max(0.0, 1.0 - dist / 2.0)
            chunks.append({
                "text": doc,
                "source": meta.get("source_file", "unknown"),
                "score": round(score, 3),
                "metadata": meta,
            })

        # Only return relevant chunks
        chunks = [c for c in chunks if c["score"] > 0.3]
        logger.info("Retrieved %d chunks for: %s", len(chunks), query[:50])
        return chunks

    except Exception as e:
        logger.warning("Retrieval failed: %s", e)
        return []