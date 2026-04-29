import asyncio
from app.rag.ingestor import KnowledgeIngestor
from app.rag.retriever import retrieve

# Sample A-level maths content
SAMPLE_CONTENT = """
Integration by Parts

Integration by parts is a technique used to integrate the product of two functions.
The formula is: ∫u dv = uv - ∫v du

Choosing u and dv — use the LIATE rule:
- L: Logarithmic functions (ln x)
- I: Inverse trig functions (arcsin x)
- A: Algebraic functions (x², x³)
- T: Trigonometric functions (sin x, cos x)
- E: Exponential functions (eˣ)

Choose u as whichever comes first in LIATE.

Example 1: ∫x eˣ dx
Let u = x, dv = eˣ dx
Then du = dx, v = eˣ
∫x eˣ dx = x eˣ - ∫eˣ dx = x eˣ - eˣ + C = eˣ(x - 1) + C

Example 2: ∫x sin x dx
Let u = x, dv = sin x dx
Then du = dx, v = -cos x
∫x sin x dx = -x cos x - ∫-cos x dx = -x cos x + sin x + C

The Chain Rule

The chain rule is used to differentiate composite functions.
If y = f(g(x)), then dy/dx = f'(g(x)) · g'(x)

In words: differentiate the outside function, keep the inside the same,
then multiply by the derivative of the inside.

Example 1: y = (3x + 1)⁵
Let u = 3x + 1, so y = u⁵
dy/du = 5u⁴, du/dx = 3
dy/dx = 5(3x + 1)⁴ · 3 = 15(3x + 1)⁴

Example 2: y = sin(x²)
dy/dx = cos(x²) · 2x = 2x cos(x²)

The Product Rule

Used to differentiate the product of two functions.
If y = uv, then dy/dx = u(dv/dx) + v(du/dx)

Example: y = x² sin x
Let u = x², v = sin x
du/dx = 2x, dv/dx = cos x
dy/dx = x² cos x + 2x sin x
"""


async def main():
    print("Step 1: Ingesting sample content into ChromaDB...")
    ingestor = KnowledgeIngestor()

    collection = ingestor.get_or_create_collection(
        subject="mathematics",
        exam_board="cambridge",
        exam_level="a_level",
    )

    n = ingestor.ingest_text(
        text=SAMPLE_CONTENT,
        metadata={
            "subject": "mathematics",
            "exam_board": "cambridge",
            "exam_level": "a_level",
            "doc_type": "syllabus",
            "topic": "calculus",
            "source_file": "sample_calculus.txt",
        },
        collection=collection,
    )
    print(f"Added {n} chunks\n")

    print("Step 2: Testing retrieval...")

    queries = [
        "how do I use integration by parts",
        "chain rule for composite functions",
        "LIATE rule",
    ]

    for query in queries:
        print(f"Query: '{query}'")
        chunks = await retrieve(
            query=query,
            subject="mathematics",
            exam_board="cambridge",
            exam_level="a_level",
            n_results=2,
        )
        for chunk in chunks:
            print(f"  Score: {chunk['score']} | {chunk['text'][:80]}...")
        print()


asyncio.run(main())