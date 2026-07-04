"""Groq Llama 4 Scout vision extraction for handwritten answers.

Vision uses a single model (Llama 4 Scout) — the existing 3-model fallback
chain cannot be reused because 3.3-70b and 3.1-8b are text-only. On error,
retry twice on the same model, then raise ExtractionFailed.
"""
import base64
import logging
import os
from dataclasses import dataclass

from groq import AsyncGroq

logger = logging.getLogger(__name__)

VISION_MODEL = "llama-4-scout-17b-16e-instruct"
MAX_RETRIES = 2

EXTRACTION_PROMPT = (
    "You are a careful transcriber. Extract only what the student has written "
    "as their handwritten answer. Do NOT extract the printed exam question. "
    "Preserve math notation as LaTeX (\\int, \\frac, ^2, etc.). "
    "If the student's writing is illegible, return the exact string: "
    "__ILLEGIBLE__\n"
    "Return plain text only. No commentary."
)


@dataclass
class ExtractionFailed(Exception):
    reason: str  # "illegible" | "llm_error"

    def __str__(self) -> str:
        return f"Extraction failed: {self.reason}"


async def extract_answer(photo_bytes: bytes) -> str:
    """Extract handwritten answer text from photo bytes. Raises ExtractionFailed."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await _call_vision_llm(photo_bytes)
            stripped = result.strip()
            if stripped == "__ILLEGIBLE__":
                raise ExtractionFailed(reason="illegible")
            return stripped
        except ExtractionFailed:
            raise
        except Exception as exc:
            last_error = exc
            logger.warning("Vision extraction attempt %d failed: %s", attempt, exc)
    raise ExtractionFailed(reason="llm_error") from last_error


async def _call_vision_llm(photo_bytes: bytes) -> str:
    """Single Groq Llama 4 Scout call with photo bytes as base64 data URI."""
    client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    b64 = base64.b64encode(photo_bytes).decode()
    data_uri = f"data:image/jpeg;base64,{b64}"

    response = await client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ],
        temperature=0.0,
        max_tokens=1000,
    )
    return response.choices[0].message.content or ""
