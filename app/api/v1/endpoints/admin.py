import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


@router.post("/ingest")
async def trigger_ingestion(secret: str):
    if secret != ADMIN_SECRET or not ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    from app.rag.ingestor import KnowledgeIngestor
    import asyncio

    ingestor = KnowledgeIngestor()
    collection = ingestor.get_or_create_collection(
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    # Ingest sample content to verify it works
    sample = """
    Integration by Parts
    The formula is: ∫u dv = uv - ∫v du
    Use the LIATE rule to choose u:
    L: Logarithmic, I: Inverse trig, A: Algebraic, T: Trig, E: Exponential
    
    Example: ∫x eˣ dx
    Let u = x, dv = eˣ dx
    du = dx, v = eˣ
    ∫x eˣ dx = x eˣ - ∫eˣ dx = x eˣ - eˣ + C = eˣ(x-1) + C
    
    The Chain Rule
    If y = f(g(x)), then dy/dx = f'(g(x)) · g'(x)
    
    The Product Rule
    If y = uv, then dy/dx = u(dv/dx) + v(du/dx)
    
    Differentiation from First Principles
    f'(x) = lim(h→0) [f(x+h) - f(x)] / h
    """

    n = ingestor.ingest_text(
        text=sample,
        metadata={
            "subject": "pure_mathematics",
            "exam_board": "edexcel",
            "exam_level": "a_level",
            "doc_type": "syllabus",
            "source_file": "sample_content.txt",
        },
        collection=collection,
    )

    return {
        "chunks_added": n,
        "total_chunks": collection.count(),
    }