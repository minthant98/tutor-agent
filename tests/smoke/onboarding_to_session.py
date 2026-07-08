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
    password = "ThrowAway123!"
    print(f"Smoke: registering {email}")
    reg = requests.post(
        f"{BASE}/api/v1/auth/register",
        json={"email": email, "name": "Smoke", "password": password},
        timeout=30,
    )
    reg.raise_for_status()

    # /auth/login uses OAuth2PasswordRequestForm (form-encoded), returns TokenResponse
    login = requests.post(
        f"{BASE}/api/v1/auth/login",
        data={"username": email, "password": password},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    print("Smoke: /readyz")
    ready = _get("/readyz")
    assert ready.json().get("status") == "ready", ready.text

    print("Smoke: walking onboarding wizard")
    # NOTE: /onboarding/education-system is frontend-only; education system is
    # inferred server-side from the exam_board choice. Not sent to the API.
    _post("/api/v1/onboarding/subjects", h, {"subjects": ["pure_mathematics"]})
    _post("/api/v1/onboarding/exam-board", h, {"exam_board": "edexcel"})
    _post(
        "/api/v1/onboarding/exam-date",
        h,
        {"exam_date": "2027-06-01"},
    )
    _post(
        "/api/v1/onboarding/target-grade",
        h,
        {"target_grade": "A*"},
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
    assert body.get("next_step") == "done", body

    print("Smoke: /dashboard/pure_mathematics")
    dash = _get("/api/v1/dashboard/pure_mathematics", h)
    d = dash.json()
    assert "today_focus" in d, d
    assert d["target_grade"] == "A*", d
    assert len(d["today_focus"]["segment_plan"]) == 3, d

    print("Smoke: /practice/topics")
    topics_resp = _get("/api/v1/practice/topics?subject=pure_mathematics", h)
    topics = topics_resp.json()
    assert isinstance(topics, list) and len(topics) > 0, topics

    print("Smoke: quick_practice session start")
    first_topic = topics[0]["topic_id"]
    r = requests.post(
        f"{BASE}/api/v1/sessions/start",
        json={"subject": "pure_mathematics", "session_type": "quick_practice", "topic": first_topic},
        headers=h, timeout=30,
    )
    r.raise_for_status()
    assert "session_id" in r.json()

    print("Smoke: weak_areas session start")
    r = requests.post(
        f"{BASE}/api/v1/sessions/start",
        json={"subject": "pure_mathematics", "session_type": "weak_areas"},
        headers=h, timeout=30,
    )
    r.raise_for_status()
    assert "session_id" in r.json()

    print("Smoke: drill_in session start")
    r = requests.post(
        f"{BASE}/api/v1/sessions/start",
        json={"subject": "pure_mathematics", "session_type": "drill_in", "topic": first_topic},
        headers=h, timeout=30,
    )
    r.raise_for_status()
    assert "session_id" in r.json()

    print("Smoke: /marker/next-question")
    r = requests.get(f"{BASE}/api/v1/marker/next-question", headers=h, timeout=30)
    r.raise_for_status()
    q = r.json()
    assert "question_text" in q and "mark_scheme" in q and "max_marks" in q

    print("Smoke: /marker/submissions (typed)")
    r = requests.post(f"{BASE}/api/v1/marker/submissions", json={
        "question_id": q["question_id"], "question_text": q["question_text"],
        "mark_scheme": q["mark_scheme"], "max_marks": q["max_marks"],
        "input_type": "typed", "answer_text": "x^2 + C",
    }, headers=h, timeout=30)
    r.raise_for_status()
    sub_id = r.json()["submission_id"]

    r = requests.post(f"{BASE}/api/v1/marker/submissions/{sub_id}/uploaded",
                     headers=h, timeout=30)
    r.raise_for_status()

    # Poll for graded (max 30s)
    for _ in range(30):
        time.sleep(1)
        r = requests.get(f"{BASE}/api/v1/marker/submissions/{sub_id}",
                        headers=h, timeout=30)
        r.raise_for_status()
        body = r.json()
        if body["status"] == "graded":
            assert body["feedback_json"] is not None
            assert body["grade_pct"] is not None
            break
        elif body["status"] == "error":
            raise AssertionError(f"Marker error: {body.get('error_message')}")
    else:
        raise AssertionError("Marker didn't grade in 30s")

    print("Smoke: /marker/submissions history")
    r = requests.get(f"{BASE}/api/v1/marker/submissions?limit=10",
                    headers=h, timeout=30)
    r.raise_for_status()
    assert len(r.json()) >= 1

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
