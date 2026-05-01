import hashlib
import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "tutor_edexcel_a_level_pure_mathematics"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output size


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def get_or_create_collection(client: QdrantClient) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s", COLLECTION_NAME)
    else:
        logger.info("Collection already exists: %s", COLLECTION_NAME)


class QdrantIngestor:
    def __init__(self):
        self.client = get_qdrant_client()
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        get_or_create_collection(self.client)

    def ingest_text(self, text: str, metadata: dict) -> int:
        from app.rag.ingestor import chunk_text
        chunks = chunk_text(text)
        if not chunks:
            return 0

        points = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{metadata.get('source_file', '')}_{i}_{chunk[:50]}".encode()).hexdigest()
            # Convert hex to int for Qdrant ID
            point_id = int(chunk_id[:16], 16)

            vector = self.encoder.encode(chunk).tolist()
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={**metadata, "text": chunk},
            ))

        # Upload in batches of 100
        batch_size = 100
        added = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
            )
            added += len(batch)

        return added