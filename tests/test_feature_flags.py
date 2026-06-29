# tests/test_feature_flags.py
from unittest.mock import patch
import pytest
from app.core import feature_flags as ff

@pytest.mark.asyncio
async def test_known_flag_returns_posthog_result():
    with patch.object(ff, "_posthog_check", return_value=True):
        assert await ff.is_enabled("student-1", "dashboard_v2") is True

@pytest.mark.asyncio
async def test_unknown_flag_returns_default():
    assert await ff.is_enabled("student-1", "not_a_real_flag", default=True) is True

@pytest.mark.asyncio
async def test_posthog_failure_falls_back_to_default():
    with patch.object(ff, "_posthog_check", side_effect=RuntimeError("posthog down")):
        assert await ff.is_enabled("student-1", "dashboard_v2", default=True) is True

def test_flags_registry_has_all_surfaces():
    expected = {"dashboard_v2", "onboarding_v2", "session_engine_v2", "notifications_v2", "account_v2"}
    assert expected.issubset(set(ff.FLAGS))
