import os
import json
import logging
import base64
from tenacity import retry, stop_after_attempt, wait_exponential
from langsmith import traceable
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_BASE = "https://api.groq.com/openai/v1"


class LLMError(Exception):
    pass


class LLM:
    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    @traceable(name="llm.generate", run_type="llm")
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 2048,
            "top_p": 1,
            "stop": None,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{GROQ_BASE}/chat/completions",
                headers=self._headers,
                json=payload,
            )

        if response.status_code != 200:
            logger.error("LLM error %s: %s", response.status_code, response.text)
            raise LLMError(f"LLM request failed: {response.status_code}")

        return response.json()["choices"][0]["message"]["content"]

    @traceable(name="llm.generate_json", run_type="llm")
    async def generate_json(self, prompt: str, system: str = "") -> dict:
        json_system = (
            (system + "\n\n" if system else "")
            + "IMPORTANT: Respond with valid JSON only. No preamble, no markdown fences. "
            + "Do NOT use LaTeX or backslashes inside JSON string values. "
            + "Write math as plain text e.g. 'x^2 * ln(x)' not '$x^2 \\ln(x)$'."
        )
        raw = await self.generate(prompt, system=json_system)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        # Fix invalid escape sequences
        fixed = []
        i = 0
        while i < len(raw):
            if raw[i] == '\\' and i + 1 < len(raw):
                next_char = raw[i + 1]
                if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                    fixed.append(raw[i])
                    fixed.append(raw[i + 1])
                    i += 2
                else:
                    fixed.append('\\\\')
                    i += 1
            elif ord(raw[i]) < 32 and raw[i] not in ('\n', '\r', '\t'):
                # Skip invalid control characters
                i += 1
            else:
                fixed.append(raw[i])
                i += 1
        raw = ''.join(fixed)

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("JSON parse failed. Raw output: %s", raw[:300])
            raise LLMError(f"LLM returned invalid JSON: {e}") from e

    @traceable(name="llm.vision", run_type="llm")
    async def vision(self, prompt: str, image_bytes: bytes, system: str = "") -> str:
        b64 = base64.b64encode(image_bytes).decode()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                },
            ],
        })

        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 2048,
            "top_p": 1,
            "stop": None,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{GROQ_BASE}/chat/completions",
                headers=self._headers,
                json=payload,
            )

        if response.status_code != 200:
            raise LLMError(f"Vision request failed: {response.status_code}")

        return response.json()["choices"][0]["message"]["content"]


llm = LLM()