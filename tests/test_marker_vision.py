import pytest
from unittest.mock import AsyncMock, patch
from app.services.marker import vision


CANNED_PHOTO_BYTES = b"\x00\x01\x02JPEGFAKE\x03\x04"


@pytest.mark.asyncio
async def test_extract_answer_returns_text():
    with patch.object(vision, "_call_vision_llm",
                     new=AsyncMock(return_value="\\int x^2 dx = x^3/3 + C")):
        result = await vision.extract_answer(CANNED_PHOTO_BYTES)
    assert result == "\\int x^2 dx = x^3/3 + C"


@pytest.mark.asyncio
async def test_extract_answer_illegible_raises():
    with patch.object(vision, "_call_vision_llm",
                     new=AsyncMock(return_value="__ILLEGIBLE__")):
        with pytest.raises(vision.ExtractionFailed) as exc:
            await vision.extract_answer(CANNED_PHOTO_BYTES)
    assert exc.value.reason == "illegible"


@pytest.mark.asyncio
async def test_extract_answer_retries_on_error():
    """First 2 calls fail, third succeeds → NOT called (only 2 retries total = 2 attempts)."""
    call_count = {"n": 0}

    async def flaky(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise TimeoutError("Groq timeout")
        return "answer"

    with patch.object(vision, "_call_vision_llm", side_effect=flaky):
        with pytest.raises(vision.ExtractionFailed):
            await vision.extract_answer(CANNED_PHOTO_BYTES)
    # 2 retries = 2 attempts, then fail
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_extract_answer_retry_recovers():
    """First call fails, second succeeds."""
    call_count = {"n": 0}

    async def maybe_flaky(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise TimeoutError("transient")
        return "x^2 + C"

    with patch.object(vision, "_call_vision_llm", side_effect=maybe_flaky):
        result = await vision.extract_answer(CANNED_PHOTO_BYTES)
    assert result == "x^2 + C"
    assert call_count["n"] == 2
