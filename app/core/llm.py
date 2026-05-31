import json
import logging
import base64
from typing import AsyncGenerator
from langsmith import traceable
import httpx


from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_BASE = "https://api.groq.com/openai/v1"

# Each model has its own rate-limit bucket on Groq.
# On 429, we fall through to the next one immediately.
_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class LLMError(Exception):
    pass


class LLM:
    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    async def _post(self, payload: dict, timeout: int = 30) -> dict:
        """Try each model in order. Returns parsed response JSON."""
        last_error: Exception | None = None
        for model in _MODELS:
            payload["model"] = model
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{GROQ_BASE}/chat/completions",
                        headers=self._headers,
                        json=payload,
                    )
                if response.status_code == 200:
                    if model != _MODELS[0]:
                        logger.info("Fallback model used: %s", model)
                    return response.json()
                if response.status_code == 429:
                    logger.warning("Rate limited on %s, trying next model", model)
                    last_error = LLMError(f"Rate limited: {model}")
                    continue
                logger.error("LLM error %s on %s: %s", response.status_code, model, response.text[:200])
                last_error = LLMError(f"LLM request failed: {response.status_code}")
                continue
            except httpx.TimeoutException:
                logger.warning("Timeout on %s, trying next model", model)
                last_error = LLMError(f"Timeout: {model}")
                continue
        raise last_error or LLMError("All models failed")

    @traceable(name="llm.generate", run_type="llm")
    async def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = await self._post({
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 2048,
            "top_p": 1,
            "stop": None,
        })
        return data["choices"][0]["message"]["content"]

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


    async def chat_with_tools(self, messages: list[dict], tools: list[dict]) -> dict:
        """Non-streaming call with tool support. Returns the full assistant message dict."""
        data = await self._post({
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_completion_tokens": 512,
            "top_p": 1,
        })
        return data["choices"][0]["message"]

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Stream response tokens, falling back across models on 429 or timeout."""
        payload = {
            "messages": messages,
            "temperature": 0.3,
            "max_completion_tokens": 2048,
            "top_p": 1,
            "stream": True,
        }
        last_error: Exception | None = None
        for model in _MODELS:
            payload["model"] = model
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    async with client.stream(
                        "POST",
                        f"{GROQ_BASE}/chat/completions",
                        headers=self._headers,
                        json=payload,
                    ) as response:
                        if response.status_code == 429:
                            logger.warning("Stream rate limited on %s, trying next model", model)
                            last_error = LLMError(f"Rate limited: {model}")
                            continue
                        if response.status_code != 200:
                            raise LLMError(f"Stream request failed: {response.status_code}")
                        if model != _MODELS[0]:
                            logger.info("Stream fallback model used: %s", model)
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data == "[DONE]":
                                return
                            try:
                                chunk = json.loads(data)
                                token = chunk["choices"][0]["delta"].get("content")
                                if token:
                                    yield token
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                        return  # completed successfully
            except httpx.TimeoutException:
                logger.warning("Stream timeout on %s, trying next model", model)
                last_error = LLMError(f"Timeout: {model}")
                continue
        raise last_error or LLMError("All models failed")


llm = LLM()