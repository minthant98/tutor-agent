import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pypdf import PdfReader
from app.rag.ingestor import KnowledgeIngestor

SPEC_DIR = Path("docs/edexcel/pure_math/syllabus")


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


async def main():
    ingestor = KnowledgeIngestor()
    collection = ingestor.get_or_create_collection(
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    for pdf in sorted(SPEC_DIR.glob("*.pdf")):
        print(f"Ingesting {pdf.name}...")
        text = extract_pdf_text(pdf)

        if not text.strip():
            print(f"  WARNING: No text extracted — may be scanned")
            continue

        metadata = {
            "subject":     "pure_mathematics",
            "exam_board":  "edexcel",
            "exam_level":  "a_level",
            "doc_type":    "specification",
            "year":        "2017",
            "source_file": pdf.name,
        }

        n = ingestor.ingest_text(text, metadata, collection)
        print(f"  → {n} chunks added")

    print(f"\nDone. Collection total: {collection.count()} chunks")


asyncio.run(main())