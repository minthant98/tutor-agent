import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pypdf import PdfReader
from app.rag.ingestor import KnowledgeIngestor

DOCS_ROOT = Path("docs/edexcel/pure_math")

PAST_PAPERS  = DOCS_ROOT / "past_papers"
MARK_SCHEMES = DOCS_ROOT / "mark_scheme"
MODEL_ANSWERS = DOCS_ROOT / "model_answers"


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def ingest_folder(
    ingestor: KnowledgeIngestor,
    folder: Path,
    doc_type: str,
    collection,
) -> int:
    total = 0
    for pdf in sorted(folder.glob("*.pdf")):
        print(f"  Ingesting {pdf.name}...")
        text = extract_pdf_text(pdf)
        if not text.strip():
            print(f"  WARNING: No text extracted from {pdf.name} — may be scanned")
            continue

        # Extract year from filename e.g. "June 2023 QP.pdf"
        parts = pdf.stem.split()
        year = next((p for p in parts if p.isdigit()), "unknown")

        metadata = {
            "subject":    "pure_mathematics",
            "exam_board": "edexcel",
            "exam_level": "a_level",
            "doc_type":   doc_type,
            "year":       year,
            "source_file": pdf.name,
        }

        n = ingestor.ingest_text(text, metadata, collection)
        print(f"  → {n} chunks added from {pdf.name}")
        total += n
    return total


async def main():
    print("Connecting to ChromaDB...")
    ingestor = KnowledgeIngestor()

    collection = ingestor.get_or_create_collection(
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )
    print(f"Collection: {collection.name}\n")

    total = 0

    print("Ingesting past papers...")
    total += ingest_folder(ingestor, PAST_PAPERS, "past_paper", collection)
    print()

    print("Ingesting mark schemes...")
    total += ingest_folder(ingestor, MARK_SCHEMES, "mark_scheme", collection)
    print()

    print("Ingesting model answers...")
    total += ingest_folder(ingestor, MODEL_ANSWERS, "model_answer", collection)
    print()

    print(f"Done! Total chunks ingested: {total}")
    print(f"Collection now has {collection.count()} chunks total")


asyncio.run(main())