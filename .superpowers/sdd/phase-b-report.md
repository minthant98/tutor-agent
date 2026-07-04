# Phase B Report — Exam Marker Backend Services

**Branch:** `exam-marker-v3`
**Base:** `6e1a654` (Phase A: GradedUpload model + Supabase Storage helpers)
**Head:** `ca926a3` (Task 6 orchestrator)
**Test suite:** 25/25 marker tests pass, 160/160 full regression pass.

---

## Task 3 — `question_selector.py`

**Commit:** `f574e25` — "Add marker question_selector: Qdrant retrieval + mark scheme pairing + LLM fallback"

### Approach

Adopted the previous subagent's uncommitted files (`app/services/marker/question_selector.py`, 259 lines; `tests/test_marker_question_selector.py`, 111 lines). Quality review found the code sound and the docstring analysis genuinely valuable — no rewrite needed.

### TDD evidence

- Ran existing tests against uncommitted implementation → **FAIL: `relation "graded_uploads" does not exist"`** (test DB stale; had not applied Phase A migration).
- Ran `DATABASE_URL=postgresql+asyncpg://tutor:tutor@localhost:5434/stride_test alembic upgrade head` — applied `aeaa5034fcb2_add_graded_uploads`.
- Re-ran tests → **PASS: 7/7 in 0.58s.**

### Qdrant schema verification

Previous subagent confirmed (and documented in module docstring) that current Qdrant payload schema is:

```
{text, source_file, exam_board, subject, exam_level, doc_type, year}
```

No `paper_ref`, `question_number`, or `linked_question_id` fields exist. Consequences documented in code and adopted as MVP-accepted:

- `_fetch_mark_scheme` will return `None` in production.
- `_generate_mark_scheme_llm` will run.
- `used_generated_mark_scheme` will always be `True` in prod until ingestion is enriched.

The retrieval function uses `app.rag.qdrant_retriever.retrieve` with signature `(query, subject, exam_board, exam_level, n_results, doc_types)` — verified matches the codebase.

### Concerns

- `question_id` is synthesized as `hashlib.md5(text[:200])[:16]` — stable across runs but not tied to a real paper reference. History-avoidance works within a student's own uploads but two students receiving similar chunks will not collide meaningfully. Acceptable for MVP.
- Since production always hits `_generate_mark_scheme_llm`, latency will be one extra LLM call per pick. Reviewer may want to cache generated mark schemes by `question_id`.

---

## Task 4 — `vision.py`

**Commit:** `10ce295` — "Add vision extraction via Groq Llama 4 Scout with retry"

### Groq SDK verification

Inspected `groq==0.37.1` installed via `requirements.txt`:

- `groq.types.chat.chat_completion_content_part_image_param.ChatCompletionContentPartImageParam` — a TypedDict with keys `type` and `image_url`.
- `ImageURL` TypedDict has keys `url` (required) and `detail` (optional, `'auto'|'low'|'high'`).

Confirmed the plan's shape `{"type": "image_url", "image_url": {"url": data_uri}}` matches the SDK signature exactly. No adaptation needed. Vision uses `llama-4-scout-17b-16e-instruct` ONLY — no text-model fallback.

### TDD evidence

- Wrote tests first → **FAIL: `cannot import name 'vision'`** (module missing).
- Implemented → **PASS: 4/4 in 0.15s.**

### Retry semantics

`MAX_RETRIES = 2` = **2 total attempts**. After both fail with a transient error, raises `ExtractionFailed(reason="llm_error")`. If the model returns the sentinel string `__ILLEGIBLE__`, raises `ExtractionFailed(reason="illegible")` immediately (no retry — illegibility isn't transient).

### Concerns

- `ExtractionFailed` uses `@dataclass` on `Exception`. Verified behaviour manually: `raise` / `except` / attribute access all work correctly.
- No jittered backoff between retries — Groq's 429s could benefit from that, but plan specifies simple loop.

---

## Task 5 — `grader_llm.py` + `_load_student_topic_context`

**Commit:** `cdfd1b8` — "Add grader_llm with structured feedback + student topic context (Alex memory)"

### TDD evidence

- Wrote tests first → **FAIL: `cannot import name 'grader_llm'`.**
- Implemented → **PASS: 8/8 in 0.36s.**

### Design notes

- Uses the existing 3-model text fallback via `app.core.llm.llm.generate` (Groq's 3.3-70b chain, per sub-project #1).
- `grade()` clamps `marks_awarded` to `[0, max_marks]`.
- Retries once on `json.JSONDecodeError` with a stricter prompt appendix ("Return ONLY JSON. Your previous response was invalid."). Second failure raises `GradingFailed`.
- Prompt injects `<student_history>` block only when `student_context` has meaningful content (recent_grades OR practice_mistakes OR nonzero mastery). Prompt explicitly says "Do NOT invent memories — only use what's listed" per the Alex-memory constraint.
- `_load_student_topic_context` reads the last 3 `GradedUpload` rows and current `MasteryState` for the topic; `recent_practice_mistakes` is left empty (documented as future work).

### Concerns

- MVP does not persist `topic` on `GradedUpload` (per Task 6 stopgap decision) — recent-grades filter therefore includes any recent grades within the subject, not strictly the topic. Documented inline; reviewer flagged this in the code comment.
- `_load_student_topic_context` approximates `prev_mastery` as `current - 0.10`. When `readiness_snapshots` is populated in a later task, this should be replaced with an actual historical query.
- `created_at` handling: the test row's `created_at` was naïve during unit test insert (server_default doesn't fire on flush without commit). Added a defensive `if created.tzinfo is None: created = created.replace(tzinfo=timezone.utc)` to keep the days-ago math safe.

---

## Task 6 — `orchestrator.py`

**Commit:** `ca926a3` — "Add marker orchestrator: state machine + mastery + readiness updates"

### TDD evidence

- Wrote tests first → **FAIL: `cannot import name 'orchestrator'`.**
- Implemented → **PASS: 6/6 in 0.77s.**

### State machine

`pending → extracting → grading → graded` (or `error` at any stage). Only `pending` is retriable. `_load_and_lock` uses `SELECT ... FOR UPDATE` (`.with_for_update()`) — this compiles cleanly against asyncpg.

### Grading pipeline

1. Load + lock upload (idempotency guard).
2. If `input_type == "photo"`: transition to `extracting`, fetch via `storage.generate_signed_download_url` + `httpx`, call `vision.extract_answer`, catch `ExtractionFailed` → status=`error`.
3. Transition to `grading`.
4. `topic = _infer_topic_from_upload(upload)` — MVP hardcodes `"integration_basics"` for `pure_mathematics` per constraint.
5. Load `student_context` via `grader_llm._load_student_topic_context`.
6. Compute `readiness_before` via `readiness_service.compute_readiness_pct(db, student_id, subject, "2026.1")`.
7. Call `grader_llm.grade`; on `GradingFailed` → status=`error`.
8. Apply mastery delta (see below) — returns `mastery_before`.
9. Recompute `readiness_after`.
10. Persist `marks_awarded`, `grade_pct`, and `feedback_json` including `readiness_before/after/delta`, `topic_mastery_before/after`.
11. Emit `marker_grading_succeeded` telemetry; emit `readiness_changed` if `abs(delta) > 0.1`.

### Mastery update

Matches the practice handler rule:
- `grade_pct >= 70` → `+0.15`
- `40 <= grade_pct < 70` → `+0.05`
- `grade_pct < 40` → `-0.05`

Clamped to `[0.0, 1.0]`. `total_attempts += 1`. `last_reviewed_at = now()`. Creates the row if missing (0.0 baseline, streak=0). Verified by `test_orchestrator_updates_mastery_on_graded`: 0.30 → 0.45 with `grade_pct=83.3%`, `total_attempts` 2 → 3.

### Telemetry safety

`_capture_event` wraps every call in try/except and logs on failure — a Sentry/PostHog outage will not fail grading.

### Concerns

- `_infer_topic_from_upload` is genuinely fragile — always returns `integration_basics` for `pure_mathematics`. Every submission is credited to the same topic, so mastery deltas outside that topic never fire. Explicit MVP stopgap per plan; must be replaced by persisting `topic` on `GradedUpload` (schema change) before shipping beyond Pure Maths integration questions.
- `_fetch_photo_bytes` uses `httpx.AsyncClient(timeout=30)` per call — no connection pooling. Fine for MVP scale.
- Readiness version `"2026.1"` is hardcoded — should be pulled from config once versioning is introduced.
- Idempotency test passed because the pre-set `status="graded"` triggers early-return before `grade()` is called. `_load_and_lock` uses `with_for_update()`; the returned row is the same identity SQLAlchemy is tracking, so subsequent mutations flush correctly.

---

## Verification summary

Command:
```
pytest tests/test_marker_question_selector.py tests/test_marker_vision.py \
       tests/test_marker_grader_llm.py tests/test_marker_orchestrator.py -v
```
Result: **25 passed in 1.12s.**

Regression:
```
pytest tests/ -x --ignore=tests/test_migration_regression.py --ignore=tests/smoke
```
Result: **160 passed in 16.72s.**

## Self-review checklist

- [x] `question_selector.pick_question` returns `QuestionCandidate` with `used_generated_mark_scheme` correctly set.
- [x] `vision.extract_answer` retries twice then raises `ExtractionFailed`; no text-model fallback.
- [x] `grader_llm.grade` accepts optional `student_context`; prompt includes `<student_history>` block only when non-empty.
- [x] `orchestrator.process_submission` idempotency guard works (`SELECT ... FOR UPDATE` + status-check early-return).
- [x] Mastery update matches practice handler (+0.15 / +0.05 / -0.05; clamped; total_attempts bumped; last_reviewed_at set).
- [x] Readiness before/after computed and persisted in `feedback_json`.
- [x] Telemetry wrapped in try/except (`_capture_event`).

## Open follow-ups (not in scope for Phase B)

1. Persist `topic` on `GradedUpload` to replace `_infer_topic_from_upload` stopgap.
2. Enrich Qdrant ingestion with `paper_ref`, `question_number`, `linked_question_id` so `_fetch_mark_scheme` can retrieve real mark schemes.
3. Mine `PracticeSession` for `recent_practice_mistakes` in `_load_student_topic_context`.
4. Wire `prev_mastery` in student context from `readiness_snapshots` once available.
5. Cache LLM-generated mark schemes by `question_id`.

---

## Fixes (post-review)

**Commit:** single consolidated fix commit on `exam-marker-v3`.

### Finding #1 — tz-aware `created_at` guard (already applied in Phase B impl)

`_load_student_topic_context` in `app/services/marker/grader_llm.py` already contained the correct guard:
```python
created = row.created_at
if created.tzinfo is None:
    created = created.replace(tzinfo=timezone.utc)
days_ago = (now - created).days
```
The fix was in place. Added a regression test `test_load_context_handles_tz_aware_datetime_from_committed_row` in `tests/test_marker_grader_llm.py` that commits a `GradedUpload` row (so `server_default` fires and `created_at` is tz-aware from Postgres), then calls `_load_student_topic_context` and asserts no exception and at least one grade returned.

### Finding #2 — `used_generated_mark_scheme` column + orchestrator fix

- Added `used_generated_mark_scheme: Mapped[bool]` column to `GradedUpload` in `app/db/models.py` with `server_default=sa.text("false")` so existing rows get `False`.
- Created Alembic migration `f1a2b3c4d5e6_add_used_generated_mark_scheme_to_graded_uploads.py` (revises `aeaa5034fcb2`). Applied cleanly against test DB via `alembic upgrade head`.
- Updated orchestrator's `feedback_json` assembly in `app/services/marker/orchestrator.py` to read `upload.used_generated_mark_scheme` instead of hardcoding `False`.
- Updated `tests/test_models_smoke.py` to assert `"used_generated_mark_scheme"` in the expected column set.
- Added `test_orchestrator_feedback_json_reflects_used_generated_mark_scheme` in `tests/test_marker_orchestrator.py` — sets `used_generated_mark_scheme=True` on the upload, processes it, and asserts `feedback_json["used_generated_mark_scheme"] is True`.

**Verification:** 21/21 targeted tests pass; 162/162 full regression pass (2 new tests added).

### Phase C endpoint constraint

Phase C endpoint constraint: `POST /marker/submissions` MUST persist `used_generated_mark_scheme` from the request body to the `GradedUpload` row. Schema is `SubmissionCreateIn.used_generated_mark_scheme: bool = False`. The reviewer will confirm at Phase C review time.
