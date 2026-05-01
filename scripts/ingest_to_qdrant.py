import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pypdf import PdfReader
from app.rag.qdrant_ingestor import QdrantIngestor

DOCS_ROOT = Path("docs/edexcel/pure_math")

def extract_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        print(f"  WARNING: Could not extract {path.name}: {e}")
        return ""


def ingest_folder(ingestor: QdrantIngestor, folder: Path, doc_type: str) -> int:
    if not folder.exists():
        return 0
    total = 0
    for pdf in sorted(folder.glob("*.pdf")):
        print(f"  Ingesting {pdf.name}...")
        text = extract_pdf_text(pdf)
        if not text.strip():
            print(f"  WARNING: No text from {pdf.name}")
            continue
        parts = pdf.stem.split()
        year = next((p for p in parts if p.isdigit()), "unknown")
        metadata = {
            "subject": "pure_mathematics",
            "exam_board": "edexcel",
            "exam_level": "a_level",
            "doc_type": doc_type,
            "year": year,
            "source_file": pdf.name,
        }
        n = ingestor.ingest_text(text, metadata)
        print(f"  -> {n} chunks added")
        total += n
    return total


async def main():
    print("Connecting to Qdrant Cloud...")
    ingestor = QdrantIngestor()
    print("Connected!\n")

    total = 0

    print("Ingesting past papers...")
    total += ingest_folder(ingestor, DOCS_ROOT / "past_papers", "past_paper")

    print("\nIngesting mark schemes...")
    total += ingest_folder(ingestor, DOCS_ROOT / "mark_scheme", "mark_scheme")

    print("\nIngesting model answers...")
    total += ingest_folder(ingestor, DOCS_ROOT / "model_answers", "model_answer")

    print("\nIngesting syllabus...")
    total += ingest_folder(ingestor, DOCS_ROOT / "syllabus", "specification")

    print(f"\nDone! Total chunks ingested: {total}")


asyncio.run(main())
