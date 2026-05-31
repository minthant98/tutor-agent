"""
Universal ingestion script for all exam boards and subjects.

Usage:
  python scripts/ingest_docs.py --board edexcel --subject pure_mathematics --level a_level
  python scripts/ingest_docs.py --board cambridge --subject mathematics --level a_level
  python scripts/ingest_docs.py --board ib --subject mathematics --level ib_hl

Expects PDFs in:
  docs/<board>/<subject>/past_papers/
  docs/<board>/<subject>/mark_schemes/
  docs/<board>/<subject>/syllabus/
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pypdf import PdfReader
from app.rag.qdrant_ingestor import QdrantIngestor, COLLECTION_NAME

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DOCS_ROOT = Path("docs")

DOC_TYPE_DIRS = {
    "past_paper":    ["past_papers", "past_paper"],
    "mark_scheme":   ["mark_schemes", "mark_scheme"],
    "syllabus":      ["syllabus", "specification", "subject_guide"],
    "textbook":      ["textbook", "textbooks"],
    "model_answer":  ["model_answers", "model_answer"],
}


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def ingest_folder(ingestor: QdrantIngestor, folder: Path, doc_type: str, metadata_base: dict) -> int:
    total = 0
    pdfs = sorted(folder.rglob("*.pdf"))
    if not pdfs:
        logger.info("  No PDFs found in %s", folder)
        return 0

    for pdf in pdfs:
        logger.info("  Ingesting %s...", pdf.name)
        text = extract_pdf_text(pdf)
        if not text.strip():
            logger.warning("  WARNING: No text in %s — may be scanned image PDF", pdf.name)
            continue

        parts = pdf.stem.split()
        year = next((p for p in parts if p.isdigit() and len(p) == 4), "unknown")
        # Capture paper component from parent folder name (e.g. pure_1, pure_2)
        component = pdf.parent.name if pdf.parent != folder else ""

        metadata = {
            **metadata_base,
            "doc_type": doc_type,
            "year": year,
            "component": component,
            "source_file": pdf.name,
        }

        n = ingestor.ingest_text(text, metadata)
        logger.info("  → %d chunks from %s", n, pdf.name)
        total += n
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", required=True, choices=["edexcel", "cambridge", "ib", "aqa", "ocr"])
    parser.add_argument("--subject", required=True, help="e.g. pure_mathematics, mathematics")
    parser.add_argument("--level", default="a_level", help="e.g. a_level, ib_hl, ib_sl, igcse")
    parser.add_argument("--docs-dir", help="Override default docs/<board>/<subject> path")
    args = parser.parse_args()

    base_dir = Path(args.docs_dir) if args.docs_dir else DOCS_ROOT / args.board / args.subject
    if not base_dir.exists():
        logger.error("Directory not found: %s", base_dir)
        logger.error("Create it and add PDFs in past_papers/, mark_schemes/, syllabus/ subfolders.")
        sys.exit(1)

    logger.info("Connecting to Qdrant collection: %s", COLLECTION_NAME)
    ingestor = QdrantIngestor()

    metadata_base = {
        "exam_board": args.board,
        "subject": args.subject,
        "exam_level": args.level,
    }

    total = 0
    for doc_type, possible_dirs in DOC_TYPE_DIRS.items():
        for dir_name in possible_dirs:
            folder = base_dir / dir_name
            if folder.exists():
                logger.info("\nIngesting %s from %s...", doc_type, folder)
                total += ingest_folder(ingestor, folder, doc_type, metadata_base)
                break

    logger.info("\nDone! Total chunks ingested: %d", total)


if __name__ == "__main__":
    main()
