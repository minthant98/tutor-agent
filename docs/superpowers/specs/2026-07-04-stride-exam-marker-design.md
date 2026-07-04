# Stride Exam Marker — Sub-project #3

**Status:** Design approved, awaiting implementation plan
**Date:** 2026-07-04
**Author:** Min Thant Tin (with Claude)
**Scope:** Sub-project #3 of 5 in the wider Stride UX overhaul
**Depends on:** Sub-project #1 (shell + segment engine + Qdrant retrieval infrastructure)

---

## 1. Context

Sub-projects #1 and #2 shipped the dashboard-first shell, adaptive session engine, and user-initiated Practice modes. Exam Marker is the headline differentiator: students upload their own written answer to a real past-paper question and get it graded like an examiner would — marks awarded per criterion, examiner-style feedback, specific improvement tip.

The differentiation isn't the grading itself (LLMs can grade). It's the sourcing loop: real Edexcel/Cambridge past-paper questions from the Qdrant index paired with the real mark scheme from the same paper. Grading is authoritative, not simulated.

Sub-project #3 is deliberately scoped standalone — it does NOT plug into the segment engine. Grading is a single-shot upload/extract/grade flow, not a conversational session. Reusing the engine would force-fit segments into a workflow that doesn't need them.

## 2. Goals & non-goals

### Goals

1. Students can submit a photo of handwritten work OR type their answer directly and get it graded against a real past-paper mark scheme
2. Question served by Stride, not provided by the student — pulled from Qdrant based on student weakness (default) or explicit topic override
3. Grading returns structured feedback: marks awarded, per-criterion breakdown with M1/A1/B1 codes, summary, one specific improvement tip
4. History surface — students can revisit past graded work at `/mark/history`
5. Free tier gets 5 monthly submissions; Pro gets unlimited (drives conversion)
6. Photos auto-delete after 90 days; grade records persist forever
7. Feature-flag gated (`marker_v2`) for kill-switch

### Non-goals (deliberate)

- PDF paper upload (multi-page + question-selection UI)
- Combined "photo of question + answer in one shot" — student writes on paper AFTER Stride shows the question
- Multi-subject expansion (still `pure_mathematics` only for MVP)
- Teacher / parent view of student's marked work
- Real-time feedback while student is writing
- Timed exam mode with marker integration
- Practice-vs-Marker unified card (kept as separate dashboard entries; revisit if it feels cluttered post-launch)

## 3. Approach

**Approach A — Standalone surface + async job with polling.**

New `/mark` route, new `graded_uploads` table, dedicated `app/services/marker/` package with question-selector + vision + grader + orchestrator sub-modules. Upload flow: client uploads photo directly to Supabase Storage via signed PUT URL (backend never proxies bytes); backend runs the vision + grading pipeline in a FastAPI `BackgroundTasks` task; frontend polls the submission row every 1s until `status=graded`.

Rejected alternatives:
- **Session engine integration** (`session_type=exam_marker`): the segment engine assumes streaming conversations. A single-shot upload-grade flow force-fits into that model.
- **Synchronous request-response** grading: 4-8s Groq latency leaves the browser hanging; timeout risk on slow phones.
- **SSE streaming grading progress**: only 2-3 stages (extracting → grading → done), which isn't rich enough to justify the SSE infra.

## 4. Data model + Supabase Storage

### New table `graded_uploads`

```sql
CREATE TABLE graded_uploads (
    id                UUID PRIMARY KEY,
    student_id        UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject           TEXT NOT NULL,              -- "pure_mathematics"
    exam_board        TEXT NOT NULL,              -- "edexcel" | "cambridge"
    question_id       TEXT NOT NULL,              -- Qdrant point id (traceable to source)
    question_text     TEXT NOT NULL,              -- cached from Qdrant retrieval
    mark_scheme       TEXT NOT NULL,              -- cached from Qdrant retrieval
    max_marks         INT NOT NULL,               -- parsed from mark scheme
    input_type        TEXT NOT NULL,              -- "photo" | "typed"
    photo_path        TEXT NULL,                  -- "{student_id}/{submission_id}.{ext}" in bucket
    answer_text       TEXT NULL,                  -- extracted (photo) or direct (typed)
    marks_awarded     INT NULL,
    grade_pct         NUMERIC NULL,               -- marks_awarded / max_marks * 100
    feedback_json     JSONB NULL,                 -- structured feedback per criterion
    status            TEXT NOT NULL,              -- pending|extracting|grading|graded|error
    error_message     TEXT NULL,
    created_at        TIMESTAMPTZ DEFAULT now(),
    updated_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_graded_uploads_student_created
    ON graded_uploads(student_id, created_at DESC);

CREATE INDEX idx_graded_uploads_student_status
    ON graded_uploads(student_id, status);
```

**No separate rate-limit table.** Free 5/month cap is computed on demand:
```sql
SELECT count(*) FROM graded_uploads
WHERE student_id = $1
  AND date_trunc('month', created_at) = date_trunc('month', now())
```

### Supabase Storage bucket `graded_uploads`

- **Private** (never publicly readable)
- **Path layout:** `{student_id}/{submission_id}.{ext}` (`.jpg`/`.jpeg`/`.png`/`.webp`)
- **Max file size:** 10 MB (rejected client-side + server-side)
- **RLS policy:**
  ```sql
  CREATE POLICY "students_read_own"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'graded_uploads'
           AND auth.uid()::text = split_part(name, '/', 1));
  ```
- **Lifecycle rule:** delete objects older than 90 days (native Supabase Storage feature)
- **Signed URLs:**
  - PUT (upload): backend generates on `POST /marker/submissions`, TTL 5 min
  - GET (viewing history): backend generates on `GET /marker/submissions/{id}`, TTL 15 min

### Migration

Single Alembic revision:
1. Creates `graded_uploads` table + 2 indexes
2. Additive only. No changes to existing tables. No DROPs.

Supabase Storage bucket + RLS policy + lifecycle rule are created **manually in the Supabase dashboard before backend deploy** (see Section 11 Rollout).

## 5. Question retrieval + selection service

**New module `app/services/marker/question_selector.py`** — one public entry point:

```python
async def pick_question(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    board: str,
    topic_override: str | None = None,
) -> QuestionCandidate

class QuestionCandidate(TypedDict):
    question_id: str      # Qdrant point id (traceable)
    question_text: str
    mark_scheme: str
    max_marks: int
    paper_ref: str        # "Edexcel 9MA0 June 2024 P1 Q3"
    topic: str
    used_generated_mark_scheme: bool  # true if mark scheme is LLM-generated fallback
```

### Selection flow

1. **Target topic:**
   - If `topic_override` provided → use it (student picked)
   - Else → reuse `_weakest_topics_with_attempts` from `app/services/planners/base.py`, limit 1
   - Else (fresh student, no mastery) → first syllabus topic in ordinal order

2. **Qdrant retrieval — past-paper question:**
   - Payload filter: `exam_board=<board>`, `subject="pure_mathematics"`, `doc_type="past_paper"`, `topic=<target>`
   - Embedding query: topic name → MiniLM vector (leverages existing embeddings)
   - Return top-10 candidates, randomize among them
   - **History-avoidance filter:** exclude `question_id` values already in `graded_uploads` for this student. If all candidates exhausted, drop this filter and log

3. **Mark scheme pairing:**
   - Each past-paper chunk carries `paper_ref` + `question_number` metadata (**assumption — see risk below**)
   - Query Qdrant filter: `doc_type="mark_scheme"`, matching `paper_ref` + `question_number`
   - If no match → skip candidate, try next
   - If ALL candidates lack mark schemes → LLM-generate a mark scheme, flag `used_generated_mark_scheme=True` in the response

4. **Extract `max_marks`:**
   - Regex first: `r"\[(\d+)\s*marks?\]"` or `r"Total:?\s*(\d+)\s*marks?"` on mark scheme text
   - If regex fails → LLM extraction with 1-shot prompt: "Return only the total mark count as an integer."
   - Default `5` if all fails (log warning)

### Risk to verify at plan-time

**Qdrant payload schema for pairing.** The design assumes past-paper + mark-scheme chunks have matched `paper_ref` and `question_number` fields. Per project memory ~34,000 chunks are ingested with `exam_board`, `subject`, `doc_type` filters. Pairing fields are not confirmed.

If pairing metadata doesn't exist, options ranked:
1. **Ship with LLM-generated mark schemes** for MVP (real questions, LLM mark schemes; flagged in UI so students know). Follow-up sub-project re-ingests with pairing metadata for authentic mark schemes.
2. **Fuzzy-match** question text against mark scheme text via embedding similarity (less reliable, mixed accuracy).
3. **Re-ingest** — scope explosion; defer.

Plan-time verification: Task 1 implementer must inspect Qdrant payload schema for a random past-paper chunk and confirm the pairing field(s). If absent, default to option 1 (LLM-generated mark schemes) and mark the UI accordingly.

## 6. Vision extraction + grading pipeline

### File layout

```
app/services/marker/
├── question_selector.py   (§5)
├── vision.py              — Groq Llama 4 Scout vision extraction
├── grader_llm.py          — grading LLM call + JSON schema
└── orchestrator.py        — pipeline glue + status transitions
```

### `vision.py` — extraction

**Public:** `async def extract_answer(photo_bytes: bytes) -> str`

- Uses Groq Llama 4 Scout directly (vision-only). The existing 3-model Groq fallback chain in `app/core/llm` cannot be reused for vision because Llama 3.3-70b and 3.1-8b are text-only — falling through would send image content to a model that ignores it. Vision path: single model, retry up to 2 times on Groq 429/timeout, then hard fail. Non-vision (grading) still uses the full 3-model fallback chain
- Prompt:
  ```
  You are a careful transcriber. Extract only what the student has written
  as their handwritten answer. Do NOT extract the printed exam question.
  Preserve math notation as LaTeX (\int, \frac, ^2, etc.).
  If the student's writing is illegible, return the exact string:
  __ILLEGIBLE__
  Return plain text only. No commentary.
  ```
- After 2 retries, if Llama 4 Scout returns `__ILLEGIBLE__` OR throws → extraction fails → orchestrator sets `status=error`

### `grader_llm.py` — grading

**Public:** `async def grade(question, mark_scheme, answer, max_marks) -> GradingResult`

- Uses Groq (any model in the chain; vision not needed for grading)
- Prompt (examiner persona):
  ```
  You are a chief examiner marking an A-Level maths past-paper answer.
  Grade strictly against the mark scheme. Award marks only when the
  student demonstrates the required step. Codes: M1 (method mark),
  A1 (accuracy mark), B1 (independent mark).

  Return ONLY a valid JSON object matching this exact schema — no other text:
  {
    "marks_awarded": <int 0..max_marks>,
    "criteria": [
      {"code": "M1|A1|B1", "description": "<what this mark rewards>",
       "awarded": <bool>, "comment": "<why or why not, 1 sentence>"}
    ],
    "summary": "<1-2 sentences on overall performance>",
    "improvement": "<one specific actionable tip for next time>"
  }
  ```

- Response parsing: `json.loads`. On `JSONDecodeError`, retry once with stricter prompt: "Return ONLY JSON. Your previous response was invalid." Second failure → orchestrator sets `status=error`
- Sanity check: `0 <= marks_awarded <= max_marks`. Clamp if outside

**`GradingResult` shape** (persisted to `graded_uploads.feedback_json`):
```json
{
  "marks_awarded": 4,
  "criteria": [
    {"code": "M1", "description": "Applied chain rule", "awarded": true,
     "comment": "Correctly identified inner and outer functions"},
    {"code": "A1", "description": "Correct derivative", "awarded": true, "comment": ""},
    {"code": "M1", "description": "Substituted correctly", "awarded": false,
     "comment": "Used x=2 instead of x=3"},
    {"code": "B1", "description": "Final numerical answer stated", "awarded": false,
     "comment": "No final answer given"}
  ],
  "summary": "Solid method setup but arithmetic slip and missing final answer.",
  "improvement": "Always box or underline your final numerical answer.",
  "used_generated_mark_scheme": false
}
```

### `orchestrator.py` — pipeline glue

**Public:** `async def process_submission(db, submission_id: UUID) -> None`

**State machine:**
```
POST /marker/submissions creates row with status="pending"
                    ↓
       BackgroundTasks starts orchestrator
                    ↓
    ┌───────────────┴───────────────┐
    │ input_type == "photo"          │ input_type == "typed"
    │  status = "extracting"          │  (skip vision)
    │  bytes = fetch from Supabase   │
    │  answer_text = vision.extract  │
    │  strip() == "__ILLEGIBLE__" → error
    └───────────────┬───────────────┘
                    ↓
        status = "grading"
        result = grader_llm.grade(...)
        marks_awarded = result["marks_awarded"]
        grade_pct = marks_awarded / max_marks × 100
        feedback_json = result
                    ↓
        status = "graded", updated_at = now
```

**Idempotency guard:** at start, `SELECT status FROM graded_uploads WHERE id=$1 FOR UPDATE`. Skip if `graded`/`extracting`/`grading` (another task might be running).

**Error paths update the row:**
- `status = "error"`
- `error_message` = user-friendly string
- Frontend polls, sees error state, shows retry button

**Latency budget:**
- Vision extraction: 2-4s (Groq Llama 4 Scout)
- Grading LLM: 2-4s
- Total: **4-8s from `pending` → `graded`** under normal load

**Background execution:**
- FastAPI `BackgroundTasks` for the initial trigger (in-process, non-persistent) — sufficient for MVP
- Failure recovery: if the process crashes mid-pipeline, a submission stays in `extracting`/`grading` state. Periodic sweeper cron (every 5 min, in Cloud Run scheduled invocation or a lightweight startup task) resets stuck rows older than 60s back to `pending` and re-triggers
- If MVP shows reliability issues, upgrade to Redis-backed queue (rq or Celery) as a follow-up. No data-model changes required

## 7. API endpoints + rate limiting

All under `app/api/v1/endpoints/marker.py` (new file, mounted at `/api/v1/marker`).

| Endpoint | Purpose |
|---|---|
| `GET /marker/next-question?topic=<optional>` | Picks a question via `question_selector.pick_question`. Returns `QuestionCandidate`. |
| `POST /marker/submissions` | Creates a submission. Body: `question_id, question_text, mark_scheme, max_marks, input_type, answer_text?`. If `input_type=photo`, backend returns `submission_id` + signed PUT `upload_url` + `upload_path`. Enforces Free 5/month cap. |
| `POST /marker/submissions/{id}/uploaded` | Frontend calls after successful direct-to-Supabase upload. Triggers `BackgroundTasks.add_task(orchestrator.process_submission, id)`. Returns 202. |
| `GET /marker/submissions/{id}` | Poll for status. Returns full row + (if graded) fresh signed GET URL for the photo. |
| `GET /marker/submissions?limit=10&offset=0` | Paginated history. Ordered by `created_at DESC`. |

### Rate limiting

New dependency `app/core/marker_limit.py`:

```python
async def check_marker_limit(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> Student:
    if student.subscription_tier == "pro":
        return student
    # Free tier: 5 per calendar month
    count = await db.execute(
        select(func.count(GradedUpload.id)).where(
            GradedUpload.student_id == student.id,
            func.date_trunc('month', GradedUpload.created_at) ==
                func.date_trunc('month', func.now()),
        )
    )
    if count.scalar() >= 5:
        raise HTTPException(
            429,
            "Free monthly limit reached — upgrade to Pro for unlimited marking."
        )
    return student
```

Applied only to `POST /marker/submissions`. Other endpoints just need auth.

### Signed URL flow (photo path)

1. Client picks a photo file
2. Client → `POST /marker/submissions` with `input_type=photo`
3. Backend inserts row (status=pending), generates a signed PUT URL for `{student_id}/{submission_id}.{ext}`, returns `submission_id`, `upload_url`, `upload_path`
4. Client uploads directly to Supabase Storage via the signed PUT URL (bytes never touch our backend)
5. Client → `POST /marker/submissions/{id}/uploaded` on success
6. Backend adds `BackgroundTasks.add_task(orchestrator.process_submission, submission_id)` and returns 202
7. Client starts polling `GET /marker/submissions/{id}`

## 8. Frontend surfaces

### New route: `/mark`

Layout (top to bottom):
- Header: `Mark my work`
- **Question card:**
  - Question text (KaTeX-rendered for math)
  - Badge: `[X marks]`
  - Small link top-right: `Change topic ▾` → topic picker modal (reuses field component from Quick Practice modal)
- **Answer input area with tab switcher:**
  - `[Type answer]` tab: textarea + KaTeX preview below; submit disabled when empty
  - `[Upload photo]` tab: file input `<input type="file" accept="image/*" capture="environment">` opens native camera on mobile; drag/drop on desktop; thumbnail preview after selection with `Retake` and `Confirm` buttons
- `Submit for marking` button
- **After submit:**
  - Progress card: `Grading your answer…` with subtle animated indicator
  - Poll `GET /marker/submissions/{id}` every 1s
  - `status=extracting` → "Reading your answer…"
  - `status=grading` → "Grading against the mark scheme…"
  - `status=graded` → transition to results view (in place, no navigation)
  - `status=error` → error card with `Retry` (re-POSTs for photo, or fresh submission for typed) or `Start over` (fresh question)

### Results view (rendered in place at `/mark`)

- **Grade banner:** `4 / 6 marks · 67%` (color-coded: red < 40%, amber 40-70%, emerald ≥ 70%)
- **Question** at top, collapsible (default collapsed)
- **Criteria list** — each row:
  - `✓` (emerald) or `✗` (slate) icon
  - `[M1] Applied chain rule` — code + description
  - Comment: `Correctly identified inner and outer functions`
- **Summary** paragraph in accent card
- **Improvement tip** in secondary card: `To improve: Always box or underline your final numerical answer.`
- **`View your answer`** link — expands to show photo (via fresh signed URL) or extracted text
- **Two CTAs at bottom:**
  - `Mark another question` → resets to fresh question fetch
  - `Return to dashboard` → routes to `/dashboard`

### History route: `/mark/history`

- Paginated list, 10 per page
- Each row: `2026-07-04 · Integration Basics · 4/6 (67%)` — click routes to `/mark/history/{id}` (read-only results view; same component as above but no CTAs, adds `Back to history` link)
- Empty state: "No marked work yet. Head over to Mark my work to try it."

### Dashboard entry point

New card `MarkMyWorkCard` — separate from PracticeCard, placed **below PracticeCard, above RecentActivity**:

```
Mark my work
Get your written work graded like an examiner would.

[Mark my work]                        Free: 2/5 this month
```

- Free tier: show remaining submissions in the corner (e.g., `Free: 2/5 this month`)
- Pro tier: hide the counter
- Card wrapped in `<FeatureFlag flag="marker_v2" fallback={null}>`

### Mobile considerations

- File input with `capture="environment"` opens native camera on iOS Safari + Android Chrome
- Photo size pre-check on the client (JPEG/PNG, ≤10 MB) — reject inline with a clear error
- The 2-tab switcher (Type / Photo) stacks vertically at `<640px` if needed; tabs work fine at typical mobile widths

### Feature flag

`marker_v2` (PostHog). Default `true`. Gates:
- Frontend: `MarkMyWorkCard` on dashboard + `/mark` route + `/mark/history` route (route-level redirect to `/dashboard` when flag off)
- Backend: no flag check — if UI doesn't send traffic, no cost

### Error UX matrix

| Error | User sees |
|---|---|
| Photo too large | "Photo must be under 10 MB — try a smaller version" (inline, before upload) |
| Upload fails | "Upload interrupted — retry" button |
| Vision returns `__ILLEGIBLE__` | "Couldn't read your answer — try a clearer photo?" with `Retake photo` button |
| Grading LLM invalid JSON twice | "Grading service is having trouble right now — retry?" |
| Free quota exceeded | Modal: "You've used all 5 free submissions this month. Upgrade to Pro for unlimited marking." + `[Upgrade to Pro]` routes to `/account#billing` |

## 9. Observability

### New PostHog events

| Event | Fires when | Properties |
|---|---|---|
| `marker_question_served` | `GET /marker/next-question` succeeds | `subject, board, topic, question_id, paper_ref, from_history_avoidance, used_generated_mark_scheme` |
| `marker_submission_created` | `POST /marker/submissions` succeeds | `input_type` (`photo`\|`typed`), `subscription_tier`, `monthly_count` |
| `marker_extraction_succeeded` | Vision returns non-illegible text | `submission_id, extracted_char_count, model_used` |
| `marker_extraction_failed` | Vision returns `__ILLEGIBLE__` or throws | `reason` (`illegible`\|`llm_error`) |
| `marker_grading_succeeded` | `status=graded` | `marks_awarded, max_marks, grade_pct, criteria_count, used_generated_mark_scheme` |
| `marker_grading_failed` | `status=error` | `error_stage` (`vision`\|`grading`), `model_used`, `error_message` |
| `marker_quota_hit` | Free student's 6th monthly attempt returns 429 | `subject` |
| `marker_history_viewed` | Frontend renders `/mark/history` | `page, submission_count` |
| `marker_retake_photo_clicked` | Frontend Retake after illegible | (none) |
| `marker_retry_clicked` | Frontend Retry after grading error | `stage` (`extraction`\|`grading`) |

### Sentry integration

- Existing Sentry SDK already catches unhandled exceptions in FastAPI routes and background tasks
- Set contextual tags in `orchestrator.process_submission`: `sentry_sdk.set_tag("submission_id", str(id))`, `set_tag("marker_stage", stage)`
- Signed URL generation failures tagged separately (`marker_stage=signed_url`)

### Health check extension

`/readyz` gains one check: Supabase Storage bucket `graded_uploads` reachable.

```python
try:
    supabase_client.storage.get_bucket("graded_uploads")
except Exception:
    failures.append("supabase_storage_bucket_missing")
```

## 10. Testing

### Unit tests

- `tests/test_marker_question_selector.py` — topic selection (weakest / override / fresh-student fallback), mocked Qdrant retrieval, mark-scheme pairing, `_extract_max_marks` regex + LLM fallback, history-avoidance filter
- `tests/test_marker_vision.py` — `extract_answer` with canned bytes + mocked LLM (happy path, `__ILLEGIBLE__` return, LLM throws)
- `tests/test_marker_grader_llm.py` — grading with mocked LLM (JSON schema validation, `marks_awarded` clamping to `0..max_marks`, invalid-JSON single retry, second-failure raises)
- `tests/test_marker_orchestrator.py` — state transitions (pending → extracting → grading → graded), idempotency guard, error paths

### Integration tests (`tests/test_marker_endpoints.py`)

- Full typed-answer flow: `GET /next-question` → `POST /submissions` (typed) → poll `GET /submissions/{id}` until `graded` → assert `marks_awarded, feedback_json, grade_pct`
- Full photo flow: mock Supabase upload; `POST /submissions` returns `upload_url`; call `/{id}/uploaded`; poll to graded; assert extracted `answer_text` present
- Free tier rate limit: create 5 submissions, 6th returns 429; upgrade user to Pro; 7th succeeds
- History pagination: 12 submissions → page 1 returns 10, page 2 returns 2, ordered by `created_at DESC`
- History isolation: student A's history excludes student B's submissions
- Signed URL: `GET /submissions/{id}` for a graded photo submission returns a signed URL expiring ~15 min later

### Manual QA checklist

- Fresh student → `/mark` → served question loads with KaTeX math → topic-override modal → typed answer → grade → results
- Photo path on real phone camera (iOS Safari + Android Chrome): tap `Upload photo` → native camera → capture → thumbnail preview → confirm → submit → grade
- Illegible photo: submit noise image → error state → `Retake` button starts fresh photo picker
- Free quota exceeded: 5 submissions → 6th shows upgrade modal
- History: view `/mark/history` → click a past row → read-only results view

## 11. Rollout

### Prerequisites (before backend deploy)

1. **Create Supabase Storage bucket `graded_uploads`** (private, via Supabase dashboard or `supabase storage create-bucket`)
2. **Add RLS policy:**
   ```sql
   CREATE POLICY "students_read_own"
     ON storage.objects FOR SELECT
     USING (bucket_id = 'graded_uploads'
            AND auth.uid()::text = split_part(name, '/', 1));
   ```
3. **Add lifecycle rule:** delete objects older than 90 days (Supabase Storage → bucket settings)
4. **Add Cloud Run env vars:**
   - `SUPABASE_STORAGE_BUCKET=graded_uploads`
   - `SUPABASE_URL=<existing>`
   - `SUPABASE_SERVICE_ROLE_KEY=<service role key from Supabase project settings>`

### Deploy order (same pattern as #1 + #2)

1. **Backend deploy** (Cloud Build + Cloud Run). Migration runs at container startup — creates `graded_uploads` table
2. **`/readyz`** returns 200 (new bucket check passes)
3. **Seed / infra sanity checks:**
   - `psql $SUPABASE_URL -c "\d graded_uploads"` — table exists with expected columns
   - Supabase dashboard → Storage → bucket exists, RLS policy attached, lifecycle rule configured
4. **Smoke test** — extended with marker probes (see spec §10 for the added smoke code)
5. **Frontend deploy** (Vercel auto-deploys on push to main)
6. **PostHog:** create `marker_v2` flag, default `true` for all users

### Rollback levers (in order)

1. **PostHog flag off** — `marker_v2 = false`. Dashboard card disappears; `/mark` and `/mark/history` redirect to `/dashboard`. Backend endpoints unreachable from UI. <30s
2. **Cloud Run revision pin** — swings traffic to previous revision. Safe because migration is additive
3. **Vercel instant rollback** — via Vercel dashboard

Migration is additive; old code reads from unchanged tables. Safe to roll back.

## 12. Out of scope deliberately

- PDF paper upload (multi-page + question-selection UI) — deferred
- Combined "photo of question + student answer in one shot" — deferred
- Multi-subject expansion (still `pure_mathematics` only)
- Teacher / parent view of marked work — future B2B surface
- Sharing marked work to social — no
- Handwriting recognition training feedback loop — future
- Timed exam mode with marker integration — future
- Real-time feedback while student is writing — no
- Practice-vs-Marker unified surface — kept separate for MVP

## 13. Open questions for plan-time

- **Qdrant payload schema** — confirm past-paper + mark-scheme chunks have `paper_ref` and `question_number` fields for pairing. If absent, ship MVP with LLM-generated mark schemes and a `used_generated_mark_scheme` flag in the UI (§5 risk)
- **Groq vision content format** — verify Groq's OpenAI-compatible API accepts `image_url` type content in the chat completions endpoint for Llama 4 Scout. If not, base64 data URI is the fallback
- **Supabase Storage lifecycle rule** — confirm the Supabase dashboard supports native 90-day auto-delete via the UI, or if we need to write our own cron
- **Signed URL library** — confirm which Supabase Python SDK version is in `requirements.txt` (v2.x has the `storage.from_.create_signed_upload_url` method; v1.x doesn't). Upgrade if needed
- **PostHog event property size** — `feedback_json.criteria` array can grow. Confirm PostHog handles up to ~1KB event payload without truncation, or downgrade to just summary metrics on the event
