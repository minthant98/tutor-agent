import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.core.config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def get_chroma_client():
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )


def collection_name(subject: str, exam_board: str, exam_level: str) -> str:
    return f"tutor_{exam_board}_{exam_level}_{subject}".replace("-", "_")


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


def doc_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


class KnowledgeIngestor:

    def __init__(self):
        self.client = get_chroma_client()
        self.ef = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def get_or_create_collection(self, subject: str, exam_board: str, exam_level: str):
        name = collection_name(subject, exam_board, exam_level)
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.ef,
            metadata={
                "subject": subject,
                "exam_board": exam_board,
                "exam_level": exam_level,
            },
        )

    def ingest_text(self, text: str, metadata: dict, collection) -> int:
        chunks = chunk_text(text)
        if not chunks:
            return 0

        ids = [f"{doc_hash(text)}_{i}" for i, _ in enumerate(chunks)]
        metadatas = [metadata] * len(chunks)

        # Check which IDs already exist
        existing = set(collection.get(ids=ids)["ids"])
        new_indices = [i for i, id_ in enumerate(ids) if id_ not in existing]

        if not new_indices:
            logger.info("All chunks already exist — skipping")
            return 0

        collection.add(
            ids=[ids[i] for i in new_indices],
            documents=[chunks[i] for i in new_indices],
            metadatas=[metadatas[i] for i in new_indices],
        )
        logger.info("Added %d chunks", len(new_indices))
        return len(new_indices)

    def ingest_text_file(self, path: Path, metadata: dict, collection) -> int:
        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata["source_file"] = path.name
        return self.ingest_text(text, metadata, collection)