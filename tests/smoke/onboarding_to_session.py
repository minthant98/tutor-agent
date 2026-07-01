"""Post-deploy smoke test for the UX overhaul sub-project #1.

Walks a throwaway test user through the full onboarding wizard via API,
then hits the dashboard and readiness probe. Fails hard if anything breaks.

Usage:
    STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app \
        python tests/smoke/onboarding_to_session.py
"""
from __future__ import annotations

import os
import sys
import time

import requests

BASE = os.environ.get("STRIDE_API_BASE", "http://localhost:8000")


def _post(path: str, headers: dict, json: dict) -> requests.Response:
    r = requests.post(f"{BASE}{path}", json=json, headers=headers, timeout=30)
    r.raise_for_status()
    return r


def _get(path: str, headers: dict | None = None) -> requests.Response:
    r = requests.get(f"{BASE}{path}", headers=headers or {}, timeout=30)
    r.raise_for_status()
    return r


def main() -> None:
    email = f"smoke+{os.getpid()}.{int(time.time())}@test.stride"
    print(f"Smoke: registering {email}")
    reg = requests.post(
        f"{BASE}/api/v1/auth/register",
        json={"email": email, "name": "Smoke", "password": "ThrowAway123!"},
        timeout=30,
    )
    reg.raise_for_status()
    token = reg.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    print("Smoke: /readyz")
    ready = _get("/readyz")
    assert ready.json().get("status") == "ready", ready.text

    print("Smoke: walking onboarding wizard")
    _post("/api/v1/onboarding/education-system", h, {"system": "a_level"})
    _post("/api/v1/onboarding/subjects", h, {"subjects": ["pure_mathematics"]})
    _post("/api/v1/onboarding/exam-board", h, {"exam_board": "edexcel"})
    _post(
        "/api/v1/onboarding/exam-date",
        h,
        {"subject_dates": {"pure_mathematics": "2027-06-01"}},
    )
    _post(
        "/api/v1/onboarding/target-grade",
        h,
        {"subject_grades": {"pure_mathematics": {"target": "A*"}}},
    )
    _post(
        "/api/v1/onboarding/preferences",
        h,
        {
            "worked_examples": True,
            "visual": False,
            "step_by_step": True,
            "practice": False,
        },
    )
    fin = _post("/api/v1/onboarding/complete", h, {})
    body = fin.json()
    assert body.get("redirect_to") == "/dashboard", body

    print("Smoke: /dashboard/pure_mathematics")
    dash = _get("/api/v1/dashboard/pure_mathematics", h)
    d = dash.json()
    assert "today_focus" in d, d
    assert d["target_grade"] == "A*", d
    assert len(d["today_focus"]["segment_plan"]) == 3, d

    print("SMOKE OK")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"SMOKE FAIL: assertion — {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as exc:
        print(f"SMOKE FAIL: HTTP — {exc} — {exc.response.text[:400]}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: {type(exc).__name__} — {exc}", file=sys.stderr)
        sys.exit(1)
