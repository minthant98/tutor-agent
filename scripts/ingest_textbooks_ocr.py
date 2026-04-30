import asyncio
import sys
sys.path.insert(0, '.')

from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from app.rag.ingestor import KnowledgeIngestor

TEXTBOOK_DIR = Path("docs/edexcel/pure_math/textbook")
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if len(c.strip()) > 50]


async def main():
    ingestor = KnowledgeIngestor()
    collection = ingestor.get_or_create_collection(
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    for pdf in sorted(TEXTBOOK_DIR.glob("*.pdf")):
        print(f"\nProcessing {pdf.name}...")
        print("Converting pages to images (this takes a few minutes)...")

        pages = convert_from_path(str(pdf), dpi=200)
        print(f"  {len(pages)} pages found")

        full_text = ""
        for i, page in enumerate(pages):
            if i % 20 == 0:
                print(f"  OCR page {i+1}/{len(pages)}...")
            text = pytesseract.image_to_string(page)
            full_text += text + "\n"

        chunks = chunk_text(full_text)
        print(f"  {len(chunks)} chunks extracted")

        total_added = 0
        for j, chunk in enumerate(chunks):
            import hashlib
            chunk_id = f"textbook_{pdf.stem}_{j}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
            try:
                collection.add(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[{
                        "subject": "pure_mathematics",
                        "exam_board": "edexcel",
                        "exam_level": "a_level",
                        "doc_type": "textbook",
                        "source_file": pdf.name,
                    }]
                )
                total_added += 1
            except Exception:
                pass  # skip duplicates

        print(f"  -> {total_added} chunks added from {pdf.name}")

    print(f"\nDone. Collection total: {collection.count()} chunks")


asyncio.run(main())
