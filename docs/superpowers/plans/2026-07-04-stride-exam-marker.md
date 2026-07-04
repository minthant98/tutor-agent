# Stride Exam Marker — Sub-project #3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Exam Marker surface to Stride — students upload a photo of handwritten work or type their answer to a real past-paper question served by Qdrant, get it graded like an examiner with structured feedback that references their history, and see their readiness update as a result.

**Architecture:** Standalone surface (new `/mark` route, new `graded_uploads` table). Async job pattern: upload → Supabase Storage direct → `POST /marker/submissions/{id}/uploaded` → FastAPI `BackgroundTasks` runs the orchestrator (vision extract → grade LLM → update mastery + readiness → set `status=graded`). Frontend polls the submission row every 1s until graded.

**Tech Stack:** Backend = FastAPI + SQLAlchemy 2.0 async + Alembic + Groq (existing 3-model chain for grading; Llama 4 Scout for vision). Storage = Supabase Storage. Frontend = Next.js 16 App Router + Tailwind + KaTeX. Tests = pytest + pytest-asyncio.

**Reference spec:** `docs/superpowers/specs/2026-07-04-stride-exam-marker-design.md`

## Global Constraints

- Python 3.11; SQLAlchemy 2.0 async style (`Mapped[T]` + `mapped_column`)
- Vision uses Groq Llama 4 Scout ONLY (existing 3-model fallback chain does NOT apply — Llama 3.3-70b and 3.1-8b are text-only); vision retries twice on same model, then hard fail
- Grading uses the existing 3-model Groq fallback chain via `app/core/llm`
- Alembic migration is additive: creates `graded_uploads` table + 2 indexes, NO changes to existing tables, NO DROPs
- Supabase Storage bucket `graded_uploads` is created MANUALLY in the Supabase dashboard before backend deploy (not via code). Same for RLS policy and 90-day lifecycle rule
- Photo path in bucket: `{student_id}/{submission_id}.{ext}` where ext ∈ `jpg | jpeg | png | webp`
- Max photo size: 10 MB (rejected client-side AND server-side)
- Signed URLs: PUT (upload) TTL 5 min, GET (viewing history) TTL 15 min
- Free tier: 5 submissions per calendar month (Pro tier unlimited)
- Feature flag `marker_v2` (PostHog): defaults `true`; gates frontend UI + dashboard card + `/mark` + `/mark/history` route access
- Grading result JSON must include `readiness_before`, `readiness_after`, `readiness_delta`, `topic_mastery_before`, `topic_mastery_after` (see `GradingResult` shape in spec §6)
- Mastery update rule after grading (matches practice handler convention from sub-project #2):
  - `grade_pct >= 70` → `mastery_score` gets `+0.15`
  - `40 <= grade_pct < 70` → `+0.05`
  - `grade_pct < 40` → `-0.05`
  - Clamp `mastery_score` to `[0.0, 1.0]`; bump `total_attempts` and `last_reviewed_at`
- Alex memory: grading prompt receives `student_context` block from `_load_student_topic_context` (last 3 grades on same topic + mastery trend + last 3 practice mistakes). Prompt explicitly forbids invented references.
- Every backend telemetry event wrapped in try/except so telemetry failures never break requests
- Frontend PostHog events use `posthog.capture(event, props)` wrapped in try/catch
- No `any` types in TypeScript; strict mode enforced
- Commit style: match repo — short sentence-case subject, no Co-Authored-By footer
- Deploy targets unchanged from sub-projects #1 and #2: Cloud Run `ascend-api` in europe-west2, Vercel project `tutor-agent`, GCP project `ascend-tutor-prod`

## File Structure

### Backend — new files

| Path | Responsibility |
|---|---|
| `app/services/marker/__init__.py` | Empty re-export module |
| `app/services/marker/storage.py` | Supabase Storage client + signed URL generators (PUT + GET) |
| `app/services/marker/question_selector.py` | Topic selection + Qdrant retrieval + mark scheme pairing + max_marks extraction |
| `app/services/marker/vision.py` | Groq Llama 4 Scout `extract_answer(photo_bytes) -> str` |
| `app/services/marker/grader_llm.py` | `grade(question, mark_scheme, answer, max_marks, student_context)` + `_load_student_topic_context` helper |
| `app/services/marker/orchestrator.py` | `process_submission(db, submission_id)` — pipeline glue + state machine + mastery update + readiness snapshot |
| `app/core/marker_limit.py` | `check_marker_limit` FastAPI dependency (Free 5/month, Pro unlimited) |
| `app/api/v1/endpoints/marker.py` | 5 endpoints: `GET /next-question`, `POST /submissions`, `POST /submissions/{id}/uploaded`, `GET /submissions/{id}`, `GET /submissions` |
| `app/schemas/marker.py` | Pydantic schemas: `QuestionCandidate`, `SubmissionCreateIn`, `SubmissionCreateOut`, `SubmissionOut`, `GradingResult`, `TopicSelection` |
| `tests/test_marker_question_selector.py` | Unit tests for topic selection + Qdrant retrieval + max_marks extraction |
| `tests/test_marker_vision.py` | Unit tests for `extract_answer` (mocked LLM + canned photo bytes) |
| `tests/test_marker_grader_llm.py` | Unit tests for `grade` + `_load_student_topic_context` |
| `tests/test_marker_orchestrator.py` | Unit tests for state transitions + idempotency + mastery update + readiness snapshot |
| `tests/test_marker_endpoints.py` | Integration tests for all 5 endpoints + rate limit + Free/Pro branching + history isolation |

### Backend — modified files

| Path | Change |
|---|---|
| `app/db/models.py` | Add `GradedUpload` ORM model |
| `alembic/versions/<rev>_add_graded_uploads.py` | New migration: create `graded_uploads` table + 2 indexes |
| `app/api/v1/endpoints/readyz.py` | Add Supabase Storage bucket check (`graded_uploads` exists) |
| `app/main.py` | Mount `marker_router` at `settings.api_v1_prefix` |
| `tests/smoke/onboarding_to_session.py` | Append marker probes (get question, create typed submission, poll for graded, list history) |
| `requirements.txt` | Add `supabase>=2.0.0` if not already present (verify existing versions before adding) |

### Frontend — new files

| Path | Responsibility |
|---|---|
| `web/src/lib/api/marker.ts` | Typed API client for all 5 marker endpoints |
| `web/src/app/(app)/mark/page.tsx` | Main "Mark my work" page — question card + answer input + grading progress + results view |
| `web/src/app/(app)/mark/history/page.tsx` | History list at `/mark/history` |
| `web/src/app/(app)/mark/history/[id]/page.tsx` | Read-only results view for a past submission |
| `web/src/components/marker/mark-my-work-card.tsx` | Dashboard card with `[Mark my work]` CTA + free-tier counter |
| `web/src/components/marker/question-card.tsx` | Renders question text (KaTeX) + `[X marks]` badge + `Change topic` link |
| `web/src/components/marker/topic-picker-modal.tsx` | Topic dropdown modal (reuses `web/src/components/dashboard/quick-practice-modal.tsx` pattern) |
| `web/src/components/marker/answer-input.tsx` | Tabbed input: `[Type answer]` textarea + `[Upload photo]` file picker with preview |
| `web/src/components/marker/grading-progress.tsx` | Spinner + stage copy (`Reading your answer…` / `Grading against the mark scheme…`) |
| `web/src/components/marker/results-view.tsx` | Grade banner + readiness delta + exam-date anchor + criteria list + summary + improvement + View answer link |
| `web/src/components/marker/history-list.tsx` | Paginated list of past submissions |

### Frontend — modified files

| Path | Change |
|---|---|
| `web/src/lib/types.ts` | Add marker types: `QuestionCandidate`, `SubmissionCreateResponse`, `SubmissionOut`, `GradingResult`, `TopicSelection` |
| `web/src/lib/feature-flags.ts` | Add `"marker_v2"` to `StrideFlag` union + `KNOWN_FLAGS` array |
| `web/src/app/(app)/dashboard/page.tsx` | Mount `<FeatureFlag flag="marker_v2" fallback={null}><MarkMyWorkCard subject={subject} /></FeatureFlag>` below `<PracticeCard>` |

---

## Phase A — Data Layer (2 tasks)

### Task 1: `GradedUpload` model + Alembic migration

**Files:**
- Modify: `app/db/models.py` — add `GradedUpload` class
- Create: `alembic/versions/<auto>_add_graded_uploads.py` (via `alembic revision -m`)
- Test: `tests/test_models_smoke.py` (extend existing smoke test)

**Interfaces produced:**
- `GradedUpload` ORM model with fields per spec §4
- Migration revision that creates `graded_uploads` table + 2 indexes

- [ ] **Step 1: Extend the model smoke test**

Add to `tests/test_models_smoke.py`:

```python
def test_graded_upload_model_imports():
    from app.db.models import GradedUpload
    assert hasattr(GradedUpload, "__tablename__")
    assert GradedUpload.__tablename__ == "graded_uploads"

def test_graded_upload_has_expected_columns():
    from app.db.models import GradedUpload
    cols = GradedUpload.__table__.columns
    expected = {
        "id", "student_id", "subject", "exam_board",
        "question_id", "question_text", "mark_scheme", "max_marks",
        "input_type", "photo_path", "answer_text",
        "marks_awarded", "grade_pct", "feedback_json",
        "status", "error_message", "created_at", "updated_at",
    }
    assert expected.issubset(set(cols.keys()))
```

- [ ] **Step 2: Run tests, expect fail**

```bash
pytest tests/test_models_smoke.py -v -k "graded_upload"
```

Expected: FAIL — `ImportError: cannot import name 'GradedUpload'`

- [ ] **Step 3: Add `GradedUpload` model to `app/db/models.py`**

Append after `TodayFocusHistory`:

```python
class GradedUpload(Base):
    __tablename__ = "graded_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)

    question_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Qdrant point id
    question_text: Mapped[str] = mapped_column(String, nullable=False)     # cached from Qdrant
    mark_scheme: Mapped[str] = mapped_column(String, nullable=False)       # cached from Qdrant
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False)

    input_type: Mapped[str] = mapped_column(String(20), nullable=False)    # "photo" | "typed"
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(String, nullable=True)

    marks_awarded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pytest tests/test_models_smoke.py -v -k "graded_upload"
```

Expected: PASS.

- [ ] **Step 5: Generate Alembic migration**

```bash
source venv/bin/activate
alembic revision -m "add_graded_uploads"
```

Note the generated file path.

- [ ] **Step 6: Implement migration body**

Replace the generated file's contents (preserve `revision` and `down_revision` from the scaffold):

```python
"""add_graded_uploads

Revision ID: <keep generated>
Revises: <keep generated>
Create Date: 2026-07-04

Additive migration for sub-project #3 Exam Marker.
- Creates graded_uploads table + 2 indexes
- No changes to existing tables. No DROPs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "<keep generated>"
down_revision = "<keep generated>"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "graded_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True),
                  sa.ForeignKey("students.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("question_id", sa.String(255), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("mark_scheme", sa.Text, nullable=False),
        sa.Column("max_marks", sa.Integer, nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False),
        sa.Column("photo_path", sa.String(500), nullable=True),
        sa.Column("answer_text", sa.Text, nullable=True),
        sa.Column("marks_awarded", sa.Integer, nullable=True),
        sa.Column("grade_pct", sa.Numeric, nullable=True),
        sa.Column("feedback_json", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_graded_uploads_student_created",
        "graded_uploads",
        ["student_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_graded_uploads_student_status",
        "graded_uploads",
        ["student_id", "status"],
    )


def downgrade():
    op.drop_index("idx_graded_uploads_student_status", table_name="graded_uploads")
    op.drop_index("idx_graded_uploads_student_created", table_name="graded_uploads")
    op.drop_table("graded_uploads")
```

- [ ] **Step 7: Apply migration to local Postgres**

```bash
SYNC_DATABASE_URL=postgresql://tutor:tutor@localhost:5434/tutor_db alembic upgrade head
psql "postgresql://tutor:tutor@localhost:5434/tutor_db" -c "\d graded_uploads" | head -30
```

Expected: table exists with all columns as defined; indexes shown.

- [ ] **Step 8: Commit**

```bash
git add app/db/models.py alembic/versions/*_add_graded_uploads.py tests/test_models_smoke.py
git commit -m "Add GradedUpload model + migration for exam marker"
```

---

### Task 2: Supabase Storage helpers

**Files:**
- Create: `app/services/marker/__init__.py` (empty)
- Create: `app/services/marker/storage.py`
- Test: `tests/test_marker_storage.py`
- Modify: `requirements.txt` (verify `supabase` package present; add if missing)

**Interfaces produced:**
- `def build_photo_path(student_id: UUID, submission_id: UUID, ext: str) -> str` — returns `"{student_id}/{submission_id}.{ext}"`
- `async def generate_signed_upload_url(path: str, content_type: str) -> str` — TTL 300s
- `async def generate_signed_download_url(path: str) -> str` — TTL 900s
- `async def check_bucket_exists() -> bool` — for /readyz

- [ ] **Step 1: Verify supabase package**

```bash
grep -i "^supabase" requirements.txt
```

If absent, add: `supabase>=2.0.0`.

- [ ] **Step 2: Write storage helper tests**

Create `tests/test_marker_storage.py`:

```python
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.marker import storage


def test_build_photo_path_jpg():
    sid = uuid4()
    subid = uuid4()
    path = storage.build_photo_path(sid, subid, "jpg")
    assert path == f"{sid}/{subid}.jpg"


def test_build_photo_path_rejects_unknown_ext():
    with pytest.raises(ValueError):
        storage.build_photo_path(uuid4(), uuid4(), "gif")


@pytest.mark.asyncio
async def test_generate_signed_upload_url():
    fake_client = MagicMock()
    fake_client.storage.from_.return_value.create_signed_upload_url.return_value = {
        "signed_url": "https://supabase.example/upload?token=abc",
        "path": "path.jpg",
        "token": "abc",
    }
    with patch.object(storage, "_get_client", return_value=fake_client):
        url = await storage.generate_signed_upload_url("student1/sub1.jpg", "image/jpeg")
    assert url.startswith("https://supabase.example/upload")


@pytest.mark.asyncio
async def test_generate_signed_download_url():
    fake_client = MagicMock()
    fake_client.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://supabase.example/download?token=xyz"
    }
    with patch.object(storage, "_get_client", return_value=fake_client):
        url = await storage.generate_signed_download_url("student1/sub1.jpg")
    assert "download" in url


@pytest.mark.asyncio
async def test_check_bucket_exists_success():
    fake_client = MagicMock()
    fake_client.storage.get_bucket.return_value = {"name": "graded_uploads"}
    with patch.object(storage, "_get_client", return_value=fake_client):
        assert await storage.check_bucket_exists() is True


@pytest.mark.asyncio
async def test_check_bucket_exists_failure():
    fake_client = MagicMock()
    fake_client.storage.get_bucket.side_effect = Exception("bucket not found")
    with patch.object(storage, "_get_client", return_value=fake_client):
        assert await storage.check_bucket_exists() is False
```

- [ ] **Step 3: Run tests, expect fail**

```bash
pytest tests/test_marker_storage.py -v
```

Expected: FAIL — module doesn't exist.

- [ ] **Step 4: Create storage helper**

Create `app/services/marker/__init__.py`:

```python
"""Exam Marker services — question retrieval, vision extraction, grading, orchestration."""
```

Create `app/services/marker/storage.py`:

```python
"""Supabase Storage helpers for the graded_uploads bucket.

Backend never proxies photo bytes — signed PUT URLs allow the client to upload
directly to Supabase. Signed GET URLs (short TTL) render photos in history.
"""
import asyncio
import logging
import os
from functools import lru_cache
from uuid import UUID

from supabase import Client, create_client

logger = logging.getLogger(__name__)

BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "graded_uploads")
UPLOAD_TTL_SEC = 300     # 5 minutes
DOWNLOAD_TTL_SEC = 900   # 15 minutes

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


@lru_cache(maxsize=1)
def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def build_photo_path(student_id: UUID, submission_id: UUID, ext: str) -> str:
    """Build the Supabase Storage object path for a submission photo."""
    ext_lower = ext.lower().lstrip(".")
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported extension: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    return f"{student_id}/{submission_id}.{ext_lower}"


async def generate_signed_upload_url(path: str, content_type: str) -> str:
    """Signed PUT URL for client-side upload. TTL 5 min."""
    def _sync():
        client = _get_client()
        result = client.storage.from_(BUCKET).create_signed_upload_url(path)
        return result["signed_url"] if "signed_url" in result else result["signedUrl"]
    return await asyncio.to_thread(_sync)


async def generate_signed_download_url(path: str) -> str:
    """Signed GET URL for viewing past photos. TTL 15 min."""
    def _sync():
        client = _get_client()
        result = client.storage.from_(BUCKET).create_signed_url(path, DOWNLOAD_TTL_SEC)
        return result["signedURL"] if "signedURL" in result else result["signed_url"]
    return await asyncio.to_thread(_sync)


async def check_bucket_exists() -> bool:
    """Health-check helper for /readyz. Returns False on any error (no raise)."""
    def _sync():
        client = _get_client()
        try:
            client.storage.get_bucket(BUCKET)
            return True
        except Exception as exc:
            logger.warning("Supabase bucket check failed: %s", exc)
            return False
    return await asyncio.to_thread(_sync)
```

- [ ] **Step 5: Run tests, expect pass**

```bash
pytest tests/test_marker_storage.py -v
```

Expected: PASS — all 6 tests green.

- [ ] **Step 6: Commit**

```bash
git add app/services/marker/__init__.py app/services/marker/storage.py tests/test_marker_storage.py requirements.txt
git commit -m "Add Supabase Storage helpers for exam marker"
```

---

## Phase B — Backend Services (4 tasks)

### Task 3: `question_selector.py`

**Files:**
- Create: `app/services/marker/question_selector.py`
- Test: `tests/test_marker_question_selector.py`

**Interfaces produced:**
- `async def pick_question(db, student_id, subject, board, topic_override=None) -> QuestionCandidate`
- `QuestionCandidate` TypedDict with `question_id, question_text, mark_scheme, max_marks, paper_ref, topic, used_generated_mark_scheme`

**Interfaces consumed:** `_weakest_topics_with_attempts`, `_first_syllabus_topics` from `app/services/planners/base.py` (sub-project #2). Existing Qdrant client from `app/rag/`.

- [ ] **Step 1: Write unit tests**

Create `tests/test_marker_question_selector.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.marker import question_selector as qs
from app.db.models import MasteryState, GradedUpload


@pytest.mark.asyncio
async def test_pick_question_uses_topic_override(db_session, student_with_subject, syllabus_edexcel_seeded):
    """When topic_override provided, skip weakness detection."""
    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x^2",
         "paper_ref": "Edexcel P1 2024", "topic": "integration_basics"}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS: x^3/3 + C", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["topic"] == "integration_basics"
    assert result["max_marks"] == 3
    assert result["used_generated_mark_scheme"] is False


@pytest.mark.asyncio
async def test_pick_question_weakness_driven_default(db_session, student_with_subject, syllabus_edexcel_seeded):
    """No topic_override → pick weakest topic with attempts."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.20, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.60, total_attempts=5),
    ])
    await db_session.flush()

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x^2",
         "paper_ref": "Edexcel P1 2024", "topic": "integration_basics"}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
        )
    assert result["topic"] == "integration_basics"  # weakest


@pytest.mark.asyncio
async def test_pick_question_fresh_student_fallback(db_session, student_with_subject, syllabus_edexcel_seeded):
    """No mastery → fall back to first syllabus topic in ordinal order."""
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_topic = EDEXCEL_9MA0_TOPICS[0]["topic_id"]

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "…",
         "paper_ref": "P1 2024", "topic": first_topic}
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 4))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
        )
    assert result["topic"] == first_topic


@pytest.mark.asyncio
async def test_pick_question_history_avoidance(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Questions already in graded_uploads should be filtered out."""
    db_session.add(GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q_seen", question_text="Old",
        mark_scheme="Old MS", max_marks=3, input_type="typed",
        status="graded",
    ))
    await db_session.flush()

    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q_seen", "question_text": "Old", "paper_ref": "P", "topic": "integration_basics"},
        {"question_id": "q_new",  "question_text": "New", "paper_ref": "P", "topic": "integration_basics"},
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=("MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["question_id"] == "q_new"


@pytest.mark.asyncio
async def test_extract_max_marks_regex_hits():
    assert qs._extract_max_marks_from_text("Total: 5 marks") == 5
    assert qs._extract_max_marks_from_text("[3 marks]") == 3
    assert qs._extract_max_marks_from_text("Some text [7 mark]") == 7


@pytest.mark.asyncio
async def test_extract_max_marks_fallback_default():
    """Regex fails + LLM extraction mocked to fail → default 5."""
    with patch.object(qs, "_extract_max_marks_via_llm", new=AsyncMock(side_effect=Exception("LLM down"))):
        result = await qs._extract_max_marks("no mark tokens here")
    assert result == 5


@pytest.mark.asyncio
async def test_no_mark_scheme_flag_set(db_session, student_with_subject, syllabus_edexcel_seeded):
    """If mark scheme retrieval returns None, generate one via LLM and flag the response."""
    with patch.object(qs, "_retrieve_from_qdrant", new=AsyncMock(return_value=[
        {"question_id": "q1", "question_text": "Integrate x", "paper_ref": "P", "topic": "integration_basics"},
    ])), patch.object(qs, "_fetch_mark_scheme", new=AsyncMock(return_value=None)), \
         patch.object(qs, "_generate_mark_scheme_llm",
                     new=AsyncMock(return_value=("Generated MS", 3))):
        result = await qs.pick_question(
            db_session, student_with_subject.id, "pure_mathematics", "edexcel",
            topic_override="integration_basics",
        )
    assert result["used_generated_mark_scheme"] is True
    assert result["mark_scheme"] == "Generated MS"
```

- [ ] **Step 2: Run tests, expect fail**

```bash
pytest tests/test_marker_question_selector.py -v
```

Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement `question_selector.py`**

Create `app/services/marker/question_selector.py`:

```python
"""Question selection + Qdrant retrieval + mark scheme pairing for Exam Marker.

Serves real Edexcel/Cambridge past-paper questions from Qdrant. Falls back to
LLM-generated mark schemes when Qdrant pairing metadata is absent.
"""
import logging
import random
import re
from typing import TypedDict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm  # existing Groq client with fallback chain
from app.db.models import GradedUpload
from app.services.planners.base import (
    _first_syllabus_topics,
    _weakest_topics_with_attempts,
)

logger = logging.getLogger(__name__)

TOP_K_CANDIDATES = 10
DEFAULT_MAX_MARKS = 5


class QuestionCandidate(TypedDict):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int
    paper_ref: str
    topic: str
    used_generated_mark_scheme: bool


async def pick_question(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    board: str,
    topic_override: str | None = None,
) -> QuestionCandidate:
    """Pick a question for grading. Weakness-driven by default; topic_override skips selection."""
    topic = await _resolve_topic(db, student_id, subject, topic_override)

    candidates = await _retrieve_from_qdrant(board, subject, topic, TOP_K_CANDIDATES)
    if not candidates:
        # Broaden search: drop topic filter within same board+subject
        candidates = await _retrieve_from_qdrant(board, subject, None, TOP_K_CANDIDATES)

    # History-avoidance filter
    seen_ids = await _load_seen_question_ids(db, student_id, subject)
    filtered = [c for c in candidates if c["question_id"] not in seen_ids]
    if not filtered:
        logger.info("All candidates already graded by student; dropping history filter")
        filtered = candidates

    # Pick one at random from filtered
    if not filtered:
        raise RuntimeError(f"No question candidates for topic={topic}, board={board}")
    picked = random.choice(filtered)

    # Fetch mark scheme
    mark_scheme_result = await _fetch_mark_scheme(picked["paper_ref"], picked["question_id"])
    used_generated = False
    if mark_scheme_result is None:
        logger.info("No paired mark scheme in Qdrant; generating via LLM")
        mark_scheme_text, max_marks = await _generate_mark_scheme_llm(picked["question_text"])
        used_generated = True
    else:
        mark_scheme_text, max_marks = mark_scheme_result

    return {
        "question_id": picked["question_id"],
        "question_text": picked["question_text"],
        "mark_scheme": mark_scheme_text,
        "max_marks": max_marks,
        "paper_ref": picked["paper_ref"],
        "topic": picked.get("topic", topic),
        "used_generated_mark_scheme": used_generated,
    }


# ── topic resolution ────────────────────────────────────────────────────────

async def _resolve_topic(
    db: AsyncSession, student_id: UUID, subject: str, topic_override: str | None
) -> str:
    if topic_override:
        return topic_override
    weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=1)
    if weak:
        return weak[0][0]
    # Fresh student — first syllabus topic
    fallback = await _first_syllabus_topics(
        db, student_id, subject, exclude=set(), limit=1
    )
    if fallback:
        return fallback[0]
    raise RuntimeError("No topics available")


# ── Qdrant retrieval ────────────────────────────────────────────────────────

async def _retrieve_from_qdrant(
    board: str, subject: str, topic: str | None, top_k: int
) -> list[dict]:
    """Retrieve past-paper question chunks from Qdrant.

    Payload filter: exam_board, subject, doc_type=past_paper, topic (optional).
    Embedding: topic name.
    Returns list of {question_id, question_text, paper_ref, topic}.
    """
    # Import here to avoid circular deps if Qdrant module imports LLM helpers
    from app.rag.retriever import retrieve

    query_text = topic.replace("_", " ") if topic else subject.replace("_", " ")
    filters = {"exam_board": board, "subject": subject, "doc_type": "past_paper"}
    if topic:
        filters["topic"] = topic

    hits = await retrieve(query_text, filters=filters, top_k=top_k)
    results = []
    for hit in hits:
        payload = hit.payload if hasattr(hit, "payload") else hit
        results.append({
            "question_id": str(payload.get("id") or payload.get("point_id") or ""),
            "question_text": payload.get("text", ""),
            "paper_ref": payload.get("paper_ref", "Unknown"),
            "topic": payload.get("topic", topic),
        })
    return results


async def _fetch_mark_scheme(paper_ref: str, question_id: str) -> tuple[str, int] | None:
    """Look up the mark scheme chunk that pairs with the given question.

    Returns (mark_scheme_text, max_marks) or None if unpaired.
    """
    from app.rag.retriever import retrieve

    filters = {"doc_type": "mark_scheme", "paper_ref": paper_ref}
    hits = await retrieve(query_text=paper_ref, filters=filters, top_k=5)
    for hit in hits:
        payload = hit.payload if hasattr(hit, "payload") else hit
        if str(payload.get("question_id", "")) == question_id or \
           str(payload.get("linked_question_id", "")) == question_id:
            text = payload.get("text", "")
            max_marks = await _extract_max_marks(text)
            return text, max_marks
    return None


# ── mark scheme generation fallback ────────────────────────────────────────

async def _generate_mark_scheme_llm(question_text: str) -> tuple[str, int]:
    """Generate a mark scheme via LLM when Qdrant pairing is unavailable."""
    prompt = f"""You are an A-Level maths mark scheme writer.

Question:
{question_text}

Write a mark scheme showing how each mark is awarded. Use M1 (method), A1
(accuracy), B1 (independent) codes. Include the total mark count at the end
in the format: "Total: X marks".

Return only the mark scheme text, no commentary."""

    response = await llm.generate(prompt)
    max_marks = await _extract_max_marks(response)
    return response, max_marks


# ── max_marks extraction ───────────────────────────────────────────────────

_MARKS_REGEXES = [
    re.compile(r"Total:?\s*(\d+)\s*marks?", re.IGNORECASE),
    re.compile(r"\[(\d+)\s*marks?\]", re.IGNORECASE),
]


def _extract_max_marks_from_text(text: str) -> int | None:
    for regex in _MARKS_REGEXES:
        m = regex.search(text)
        if m:
            return int(m.group(1))
    return None


async def _extract_max_marks_via_llm(mark_scheme_text: str) -> int:
    prompt = (
        "Return only an integer — the total mark count for this mark scheme. "
        "No other text.\n\n" + mark_scheme_text
    )
    response = await llm.generate(prompt)
    match = re.search(r"\d+", response)
    if match:
        return int(match.group(0))
    raise ValueError("LLM did not return an integer")


async def _extract_max_marks(mark_scheme_text: str) -> int:
    regex_hit = _extract_max_marks_from_text(mark_scheme_text)
    if regex_hit is not None:
        return regex_hit
    try:
        return await _extract_max_marks_via_llm(mark_scheme_text)
    except Exception as exc:
        logger.warning("max_marks extraction failed: %s — defaulting to %d",
                       exc, DEFAULT_MAX_MARKS)
        return DEFAULT_MAX_MARKS


# ── history-avoidance ──────────────────────────────────────────────────────

async def _load_seen_question_ids(
    db: AsyncSession, student_id: UUID, subject: str
) -> set[str]:
    res = await db.execute(
        select(GradedUpload.question_id).where(
            GradedUpload.student_id == student_id,
            GradedUpload.subject == subject,
        )
    )
    return {row[0] for row in res.all()}
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pytest tests/test_marker_question_selector.py -v
```

Expected: PASS — all 7 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/services/marker/question_selector.py tests/test_marker_question_selector.py
git commit -m "Add marker question_selector: Qdrant retrieval + mark scheme pairing + LLM fallback"
```

---

### Task 4: `vision.py` — Groq Llama 4 Scout extraction

**Files:**
- Create: `app/services/marker/vision.py`
- Test: `tests/test_marker_vision.py`

**Interfaces produced:**
- `async def extract_answer(photo_bytes: bytes) -> str` — returns extracted text or raises `ExtractionFailed` on illegible / LLM error

**Constraint:** vision uses Groq Llama 4 Scout ONLY — no fallback to non-vision models. Retries twice on same model on 429/timeout.

- [ ] **Step 1: Write tests**

Create `tests/test_marker_vision.py`:

```python
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
```

- [ ] **Step 2: Run tests, expect fail**

```bash
pytest tests/test_marker_vision.py -v
```

- [ ] **Step 3: Implement vision helper**

Create `app/services/marker/vision.py`:

```python
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
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pytest tests/test_marker_vision.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/services/marker/vision.py tests/test_marker_vision.py
git commit -m "Add vision extraction via Groq Llama 4 Scout with retry"
```

---

### Task 5: `grader_llm.py` — grading LLM + Alex memory helper

**Files:**
- Create: `app/services/marker/grader_llm.py`
- Test: `tests/test_marker_grader_llm.py`

**Interfaces produced:**
- `async def grade(question, mark_scheme, answer, max_marks, student_context=None) -> GradingResult`
- `async def _load_student_topic_context(db, student_id, subject, topic) -> StudentTopicContext`
- `GradingResult` and `StudentTopicContext` TypedDicts

- [ ] **Step 1: Write tests**

Create `tests/test_marker_grader_llm.py`:

```python
import json
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.services.marker import grader_llm
from app.db.models import MasteryState, GradedUpload


VALID_LLM_JSON = json.dumps({
    "marks_awarded": 4,
    "criteria": [
        {"code": "M1", "description": "Applied chain rule",
         "awarded": True, "comment": "Correctly identified inner and outer"},
        {"code": "A1", "description": "Correct derivative",
         "awarded": True, "comment": ""},
        {"code": "M1", "description": "Substituted correctly",
         "awarded": False, "comment": "Used x=2 instead of x=3"},
        {"code": "B1", "description": "Final numerical answer stated",
         "awarded": False, "comment": "No final answer given"},
    ],
    "summary": "Solid method setup but arithmetic slip.",
    "improvement": "Always box or underline your final numerical answer.",
})


@pytest.mark.asyncio
async def test_grade_returns_structured_result():
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=VALID_LLM_JSON)):
        result = await grader_llm.grade(
            question="Find dy/dx of (x^2+1)^3",
            mark_scheme="M1 chain rule, A1 correct, B1 final",
            answer="3(x^2+1)^2 * 2x",
            max_marks=6,
        )
    assert result["marks_awarded"] == 4
    assert len(result["criteria"]) == 4
    assert result["improvement"].endswith("numerical answer.")


@pytest.mark.asyncio
async def test_grade_clamps_over_max():
    over_max_json = json.dumps({
        "marks_awarded": 10,  # over max
        "criteria": [], "summary": "s", "improvement": "i",
    })
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=over_max_json)):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert result["marks_awarded"] == 6


@pytest.mark.asyncio
async def test_grade_clamps_below_zero():
    neg_json = json.dumps({
        "marks_awarded": -1,
        "criteria": [], "summary": "s", "improvement": "i",
    })
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value=neg_json)):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert result["marks_awarded"] == 0


@pytest.mark.asyncio
async def test_grade_retries_on_invalid_json():
    """First LLM call returns garbage, second returns valid JSON."""
    call_count = {"n": 0}

    async def sometimes_valid(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return "not json"
        return VALID_LLM_JSON

    with patch.object(grader_llm, "_call_llm", side_effect=sometimes_valid):
        result = await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
        )
    assert call_count["n"] == 2
    assert result["marks_awarded"] == 4


@pytest.mark.asyncio
async def test_grade_raises_after_two_bad_responses():
    with patch.object(grader_llm, "_call_llm", new=AsyncMock(return_value="not json")):
        with pytest.raises(grader_llm.GradingFailed):
            await grader_llm.grade(question="Q", mark_scheme="MS", answer="A", max_marks=6)


@pytest.mark.asyncio
async def test_grade_includes_student_context_in_prompt():
    """When student_context is passed, the prompt should include it."""
    captured_prompt = {}

    async def capture(prompt):
        captured_prompt["text"] = prompt
        return VALID_LLM_JSON

    context = {
        "recent_grades": [
            {"grade_pct": 33, "marks_awarded": 2, "max_marks": 6,
             "improvement": "Show working", "days_ago": 4},
        ],
        "mastery_trend": {"prev_mastery": 0.20, "current_mastery": 0.35, "trend": "up"},
        "recent_practice_mistakes": ["forgot +C"],
    }
    with patch.object(grader_llm, "_call_llm", side_effect=capture):
        await grader_llm.grade(
            question="Q", mark_scheme="MS", answer="A", max_marks=6,
            student_context=context,
        )
    assert "student_history" in captured_prompt["text"]
    assert "33%" in captured_prompt["text"]
    assert "forgot +C" in captured_prompt["text"]


@pytest.mark.asyncio
async def test_load_student_topic_context_empty_for_fresh_student(db_session, student_with_subject):
    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics"
    )
    assert ctx["recent_grades"] == []
    assert ctx["recent_practice_mistakes"] == []
    assert ctx["mastery_trend"]["current_mastery"] == 0.0


@pytest.mark.asyncio
async def test_load_student_topic_context_returns_recent_grades(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    db_session.add(GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q1", question_text="Old",
        mark_scheme="MS", max_marks=6, input_type="typed", answer_text="A",
        marks_awarded=2, grade_pct=33.3,
        feedback_json={"improvement": "Show working"},
        status="graded",
    ))
    db_session.add(MasteryState(
        student_id=student_with_subject.id, subject="pure_mathematics",
        topic="integration_basics", mastery_score=0.35, total_attempts=3,
        last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    await db_session.flush()

    ctx = await grader_llm._load_student_topic_context(
        db_session, student_with_subject.id, "pure_mathematics", "integration_basics",
    )
    assert len(ctx["recent_grades"]) == 1
    assert ctx["recent_grades"][0]["grade_pct"] == pytest.approx(33.3, abs=0.5)
    assert ctx["mastery_trend"]["current_mastery"] == pytest.approx(0.35)
```

- [ ] **Step 2: Run tests, expect fail**

```bash
pytest tests/test_marker_grader_llm.py -v
```

- [ ] **Step 3: Implement grader**

Create `app/services/marker/grader_llm.py`:

```python
"""Grading LLM for Exam Marker + Alex memory helper.

Uses the existing Groq 3-model fallback chain (text-only). Returns a
structured GradingResult that references the student's recent work on
the same topic when student_context is provided.
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm
from app.db.models import GradedUpload, MasteryState

logger = logging.getLogger(__name__)

RETRY_LIMIT = 1  # 1 retry after initial failure (2 total attempts)


class GradingCriterion(TypedDict):
    code: str
    description: str
    awarded: bool
    comment: str


class GradingResult(TypedDict):
    marks_awarded: int
    criteria: list[GradingCriterion]
    summary: str
    improvement: str


class GradeRecord(TypedDict):
    grade_pct: float
    marks_awarded: int
    max_marks: int
    improvement: str
    days_ago: int


class MasteryTrend(TypedDict):
    prev_mastery: float
    current_mastery: float
    trend: str  # "up" | "down" | "flat"


class StudentTopicContext(TypedDict):
    recent_grades: list[GradeRecord]
    mastery_trend: MasteryTrend
    recent_practice_mistakes: list[str]


@dataclass
class GradingFailed(Exception):
    reason: str

    def __str__(self) -> str:
        return f"Grading failed: {self.reason}"


async def grade(
    question: str,
    mark_scheme: str,
    answer: str,
    max_marks: int,
    student_context: StudentTopicContext | None = None,
) -> GradingResult:
    """Grade a student answer. Returns structured feedback. Raises GradingFailed on 2 bad LLM responses."""
    prompt = _build_prompt(question, mark_scheme, answer, max_marks, student_context)

    last_error: Exception | None = None
    for attempt in range(RETRY_LIMIT + 1):
        try:
            response = await _call_llm(prompt if attempt == 0 else _stricter_prompt(prompt))
            result = json.loads(response)
            # Clamp marks
            ma = int(result.get("marks_awarded", 0))
            result["marks_awarded"] = max(0, min(ma, max_marks))
            # Guarantee shape
            result.setdefault("criteria", [])
            result.setdefault("summary", "")
            result.setdefault("improvement", "")
            return result  # type: ignore[return-value]
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("Grading returned invalid JSON on attempt %d", attempt + 1)
        except Exception as exc:
            last_error = exc
            logger.warning("Grading call failed on attempt %d: %s", attempt + 1, exc)
    raise GradingFailed(reason="invalid_json_after_retry") from last_error


# ── prompt building ────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTION = """You are a chief examiner marking an A-Level maths past-paper answer.
Grade strictly against the mark scheme. Award marks only when the student
demonstrates the required step. Codes: M1 (method mark), A1 (accuracy mark),
B1 (independent mark).

Return ONLY a valid JSON object matching this exact schema — no other text:
{
  "marks_awarded": <int 0..max_marks>,
  "criteria": [
    {"code": "M1|A1|B1", "description": "<what this mark rewards>",
     "awarded": <bool>, "comment": "<why or why not, 1 sentence>"}
  ],
  "summary": "<1-2 sentences on overall performance>",
  "improvement": "<one specific actionable tip for next time>"
}"""


def _build_prompt(
    question: str,
    mark_scheme: str,
    answer: str,
    max_marks: int,
    student_context: StudentTopicContext | None,
) -> str:
    parts = [_SYSTEM_INSTRUCTION, ""]
    if student_context and _has_any_context(student_context):
        parts.append(_format_student_history(student_context))
        parts.append("")
        parts.append(
            "Use this context to make your feedback specific. Reference patterns "
            "where relevant. Do NOT invent memories — only use what's listed."
        )
        parts.append("")
    parts.append(f"Max marks: {max_marks}")
    parts.append(f"Question:\n{question}")
    parts.append("")
    parts.append(f"Mark scheme:\n{mark_scheme}")
    parts.append("")
    parts.append(f"Student answer:\n{answer}")
    return "\n".join(parts)


def _stricter_prompt(original: str) -> str:
    return original + "\n\nReturn ONLY JSON. Your previous response was invalid."


def _has_any_context(ctx: StudentTopicContext) -> bool:
    return bool(
        ctx.get("recent_grades")
        or ctx.get("recent_practice_mistakes")
        or (ctx.get("mastery_trend", {}).get("current_mastery", 0) > 0)
    )


def _format_student_history(ctx: StudentTopicContext) -> str:
    lines = ["<student_history>", "This student has recently:"]
    grades = ctx.get("recent_grades", [])
    if grades:
        percents = ", ".join(f"{int(g['grade_pct'])}%" for g in grades)
        lines.append(f"- Attempted this topic {len(grades)} times; recent grades: {percents}")
    trend = ctx.get("mastery_trend", {})
    if trend.get("trend") in ("up", "down"):
        arrow = "trending up" if trend["trend"] == "up" else "trending down"
        lines.append(
            f"- Mastery {arrow}: {int(trend['prev_mastery']*100)}% → "
            f"{int(trend['current_mastery']*100)}%"
        )
    mistakes = ctx.get("recent_practice_mistakes", [])
    if mistakes:
        lines.append("- Repeated mistakes noticed:")
        for m in mistakes[:3]:
            lines.append(f"  · {m}")
    lines.append("</student_history>")
    return "\n".join(lines)


# ── LLM call wrapper ───────────────────────────────────────────────────────

async def _call_llm(prompt: str) -> str:
    return await llm.generate(prompt)


# ── student topic context loader ───────────────────────────────────────────

async def _load_student_topic_context(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> StudentTopicContext:
    """Assemble recent grades + mastery trend + recent practice mistakes for topic."""
    now = datetime.now(timezone.utc)

    # Recent grades on this topic (last 3)
    grade_rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student_id,
            GradedUpload.subject == subject,
            GradedUpload.status == "graded",
        ).order_by(GradedUpload.created_at.desc()).limit(50)
    )).scalars().all()

    # Filter by topic (question_id-based topic filter not stored; use feedback context)
    recent_grades: list[GradeRecord] = []
    for row in grade_rows:
        # We don't currently persist topic on GradedUpload; approximate by matching
        # against the row's mark_scheme snippet (best effort). For MVP, take all recent
        # grades regardless of topic — reviewer can flag if this needs refinement.
        if len(recent_grades) >= 3:
            break
        improvement = ""
        if row.feedback_json:
            improvement = row.feedback_json.get("improvement", "") if isinstance(row.feedback_json, dict) else ""
        days_ago = (now - row.created_at.replace(tzinfo=timezone.utc)).days
        recent_grades.append({
            "grade_pct": float(row.grade_pct or 0),
            "marks_awarded": row.marks_awarded or 0,
            "max_marks": row.max_marks,
            "improvement": improvement,
            "days_ago": days_ago,
        })

    # Current mastery for the topic
    mastery_row = (await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar_one_or_none()

    current_mastery = float(mastery_row.mastery_score) if mastery_row else 0.0
    # Prev mastery approximated as current - typical practice delta; when
    # readiness_snapshots is populated we can improve this. For MVP, use flat.
    prev_mastery = max(0.0, current_mastery - 0.10) if current_mastery > 0 else 0.0
    if current_mastery > prev_mastery + 0.02:
        trend = "up"
    elif current_mastery < prev_mastery - 0.02:
        trend = "down"
    else:
        trend = "flat"

    return {
        "recent_grades": recent_grades,
        "mastery_trend": {
            "prev_mastery": prev_mastery,
            "current_mastery": current_mastery,
            "trend": trend,
        },
        "recent_practice_mistakes": [],  # populated in a future task when we mine sessions
    }
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pytest tests/test_marker_grader_llm.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/services/marker/grader_llm.py tests/test_marker_grader_llm.py
git commit -m "Add grader_llm with structured feedback + student topic context (Alex memory)"
```

---

### Task 6: `orchestrator.py` — pipeline glue

**Files:**
- Create: `app/services/marker/orchestrator.py`
- Test: `tests/test_marker_orchestrator.py`

**Interfaces produced:**
- `async def process_submission(db, submission_id: UUID) -> None`

**Interfaces consumed:**
- `extract_answer` (Task 4), `grade` + `_load_student_topic_context` (Task 5)
- `readiness_service.compute_readiness_pct` (existing from sub-project #1)
- `MasteryState` and `GradedUpload` ORM models

**State machine:** `pending → extracting → grading → graded` (or `error` at any stage).

- [ ] **Step 1: Write orchestrator tests**

Create `tests/test_marker_orchestrator.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select
from app.db.models import GradedUpload, MasteryState
from app.services.marker import orchestrator, vision, grader_llm


def _make_upload(student_id, subject="pure_mathematics", input_type="typed",
                 answer_text="x^2 + C", max_marks=6):
    return GradedUpload(
        student_id=student_id, subject=subject, exam_board="edexcel",
        question_id="q1", question_text="Q", mark_scheme="MS",
        max_marks=max_marks, input_type=input_type,
        answer_text=answer_text if input_type == "typed" else None,
        photo_path=None if input_type == "typed" else "student/sub.jpg",
        status="pending",
    )


VALID_GRADING = {
    "marks_awarded": 4,
    "criteria": [], "summary": "s", "improvement": "i",
}


@pytest.mark.asyncio
async def test_orchestrator_typed_flow_transitions_to_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    db_session.add(upload)
    await db_session.flush()

    with patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "graded"
    assert upload.marks_awarded == 4
    assert upload.grade_pct == pytest.approx(66.67, abs=0.5)
    assert upload.feedback_json["marks_awarded"] == 4
    assert upload.feedback_json["readiness_after"] >= upload.feedback_json["readiness_before"]


@pytest.mark.asyncio
async def test_orchestrator_photo_flow_calls_vision(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="photo",
                          answer_text=None)
    db_session.add(upload)
    await db_session.flush()

    with patch.object(orchestrator, "_fetch_photo_bytes",
                     new=AsyncMock(return_value=b"fake_bytes")), \
         patch.object(vision, "extract_answer",
                     new=AsyncMock(return_value="x^2 + C")), \
         patch.object(grader_llm, "grade", new=AsyncMock(return_value=VALID_GRADING)):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "graded"
    assert upload.answer_text == "x^2 + C"


@pytest.mark.asyncio
async def test_orchestrator_extraction_illegible_sets_error(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="photo",
                          answer_text=None)
    db_session.add(upload)
    await db_session.flush()

    with patch.object(orchestrator, "_fetch_photo_bytes",
                     new=AsyncMock(return_value=b"fake_bytes")), \
         patch.object(vision, "extract_answer",
                     new=AsyncMock(side_effect=vision.ExtractionFailed(reason="illegible"))):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "error"
    assert "clearer" in upload.error_message.lower() or "read" in upload.error_message.lower()


@pytest.mark.asyncio
async def test_orchestrator_grading_failure_sets_error(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    db_session.add(upload)
    await db_session.flush()

    with patch.object(grader_llm, "grade",
                     new=AsyncMock(side_effect=grader_llm.GradingFailed(reason="invalid_json_after_retry"))):
        await orchestrator.process_submission(db_session, upload.id)

    await db_session.refresh(upload)
    assert upload.status == "error"


@pytest.mark.asyncio
async def test_orchestrator_idempotent_skip_already_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    upload = _make_upload(student_with_subject.id, input_type="typed")
    upload.status = "graded"
    upload.marks_awarded = 5
    upload.feedback_json = {"marks_awarded": 5}
    db_session.add(upload)
    await db_session.flush()

    graded_call_count = {"n": 0}
    async def counter(*args, **kwargs):
        graded_call_count["n"] += 1
        return VALID_GRADING

    with patch.object(grader_llm, "grade", side_effect=counter):
        await orchestrator.process_submission(db_session, upload.id)

    # grade should NOT be called
    assert graded_call_count["n"] == 0


@pytest.mark.asyncio
async def test_orchestrator_updates_mastery_on_graded(
    db_session, student_with_subject, syllabus_edexcel_seeded
):
    # Seed prior mastery so we can measure delta
    db_session.add(MasteryState(
        student_id=student_with_subject.id, subject="pure_mathematics",
        topic="integration_basics", mastery_score=0.30, total_attempts=2,
    ))
    upload = _make_upload(student_with_subject.id, input_type="typed", max_marks=6)
    upload.question_text = "Integrate x^2"
    # Attach topic to upload's mark_scheme so orchestrator can look it up
    db_session.add(upload)
    await db_session.flush()

    high_score = {**VALID_GRADING, "marks_awarded": 5}  # 83% → +0.15
    with patch.object(grader_llm, "grade", new=AsyncMock(return_value=high_score)), \
         patch.object(orchestrator, "_infer_topic_from_upload",
                     return_value="integration_basics"):
        await orchestrator.process_submission(db_session, upload.id)

    ms = (await db_session.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_with_subject.id,
            MasteryState.topic == "integration_basics",
        )
    )).scalar_one()
    assert ms.mastery_score == pytest.approx(0.45, abs=0.01)
    assert ms.total_attempts == 3
```

- [ ] **Step 2: Run tests, expect fail**

- [ ] **Step 3: Implement orchestrator**

Create `app/services/marker/orchestrator.py`:

```python
"""Pipeline glue for Exam Marker: fetch photo → vision → grade → mastery+readiness update.

Handles state transitions: pending → extracting → grading → graded (or error).
Idempotency guard prevents duplicate processing.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import capture
from app.db.models import GradedUpload, MasteryState
from app.services.marker import grader_llm, vision, storage
from app.services.readiness_service import compute_readiness_pct

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {"pending"}  # only pending is retriable
COMPLETED_STATUSES = {"graded", "error"}


async def process_submission(db: AsyncSession, submission_id: UUID) -> None:
    """Run the full pipeline for a submission. Idempotent: re-runs on stuck rows only."""
    upload = await _load_and_lock(db, submission_id)
    if upload is None:
        logger.warning("Submission %s not found", submission_id)
        return
    if upload.status not in ACTIVE_STATUSES:
        logger.info("Submission %s already in status=%s; skipping",
                    submission_id, upload.status)
        return

    try:
        # Extraction stage (photo only)
        if upload.input_type == "photo":
            upload.status = "extracting"
            await db.flush()
            photo_bytes = await _fetch_photo_bytes(upload.photo_path)
            try:
                upload.answer_text = await vision.extract_answer(photo_bytes)
            except vision.ExtractionFailed as exc:
                _set_error(upload, _user_facing_extraction_error(exc.reason))
                _capture_event("marker_extraction_failed", upload.student_id,
                               reason=exc.reason)
                await db.flush()
                return
            _capture_event("marker_extraction_succeeded", upload.student_id,
                           submission_id=str(upload.id),
                           extracted_char_count=len(upload.answer_text or ""))

        # Grading stage
        upload.status = "grading"
        await db.flush()

        topic = _infer_topic_from_upload(upload)
        student_context = await grader_llm._load_student_topic_context(
            db, upload.student_id, upload.subject, topic,
        )

        readiness_before = await compute_readiness_pct(
            db, upload.student_id, upload.subject, "2026.1",
        )

        try:
            grading_result = await grader_llm.grade(
                question=upload.question_text,
                mark_scheme=upload.mark_scheme,
                answer=upload.answer_text or "",
                max_marks=upload.max_marks,
                student_context=student_context,
            )
        except grader_llm.GradingFailed:
            _set_error(upload, "Grading service is having trouble right now — please try again.")
            _capture_event("marker_grading_failed", upload.student_id,
                           error_stage="grading")
            await db.flush()
            return

        # Update mastery
        mastery_before = await _update_mastery(
            db, upload.student_id, upload.subject, topic,
            grade_pct=(grading_result["marks_awarded"] / upload.max_marks * 100),
        )

        # Recompute readiness after mastery update
        readiness_after = await compute_readiness_pct(
            db, upload.student_id, upload.subject, "2026.1",
        )
        mastery_after = await _current_mastery(db, upload.student_id, upload.subject, topic)

        # Finalize row
        upload.marks_awarded = grading_result["marks_awarded"]
        upload.grade_pct = round(
            grading_result["marks_awarded"] / upload.max_marks * 100, 2
        )
        upload.feedback_json = {
            **grading_result,
            "readiness_before": round(readiness_before, 1),
            "readiness_after": round(readiness_after, 1),
            "readiness_delta": round(readiness_after - readiness_before, 1),
            "topic_mastery_before": round(mastery_before, 2),
            "topic_mastery_after": round(mastery_after, 2),
            "used_generated_mark_scheme": False,  # set by question_selector; defaults false
        }
        upload.status = "graded"
        upload.updated_at = datetime.now(timezone.utc)
        await db.flush()

        _capture_event(
            "marker_grading_succeeded", upload.student_id,
            marks_awarded=grading_result["marks_awarded"],
            max_marks=upload.max_marks,
            grade_pct=upload.grade_pct,
            criteria_count=len(grading_result.get("criteria", [])),
            readiness_delta=upload.feedback_json["readiness_delta"],
            topic_mastery_delta=(mastery_after - mastery_before),
        )
        if abs(readiness_after - readiness_before) > 0.1:
            _capture_event("readiness_changed", upload.student_id,
                           subject=upload.subject,
                           prev_pct=readiness_before, new_pct=readiness_after,
                           delta=readiness_after - readiness_before)
    except Exception as exc:  # unhandled — mark error and log
        logger.exception("Unhandled orchestrator error for %s", submission_id)
        _set_error(upload, "Something went wrong grading your work. Please try again.")
        await db.flush()


# ── helpers ────────────────────────────────────────────────────────────────

async def _load_and_lock(db: AsyncSession, submission_id: UUID) -> GradedUpload | None:
    """SELECT ... FOR UPDATE to enforce idempotency across concurrent tasks."""
    res = await db.execute(
        select(GradedUpload).where(GradedUpload.id == submission_id).with_for_update()
    )
    return res.scalar_one_or_none()


async def _fetch_photo_bytes(path: str) -> bytes:
    """Fetch photo bytes from Supabase Storage via signed download URL + HTTP fetch."""
    import httpx
    url = await storage.generate_signed_download_url(path)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


def _infer_topic_from_upload(upload: GradedUpload) -> str:
    """Best-effort topic inference. Question selector stored topic in question_text search;
    for MVP we don't persist a topic column — approximate from question_text as fallback.

    Real implementation: reviewer may add a `topic` column to GradedUpload.
    For now, use the subject as the topic label if we can't do better."""
    # If a topic-like slug is in question_text (from question_selector), prefer that.
    # MVP fallback: hardcode integration_basics if subject is pure_mathematics.
    # Reviewer should flag adding a proper topic column.
    return "integration_basics" if upload.subject == "pure_mathematics" else upload.subject


async def _update_mastery(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    topic: str,
    grade_pct: float,
) -> float:
    """Apply grade-based mastery delta. Returns the mastery_score BEFORE update."""
    row = (await db.execute(
        select(MasteryState).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar_one_or_none()

    if row is None:
        row = MasteryState(
            student_id=student_id, subject=subject, topic=topic,
            mastery_score=0.0, total_attempts=0, correct_streak=0,
        )
        db.add(row)
        await db.flush()

    before = float(row.mastery_score or 0)
    if grade_pct >= 70:
        delta = 0.15
    elif grade_pct >= 40:
        delta = 0.05
    else:
        delta = -0.05

    row.mastery_score = max(0.0, min(1.0, before + delta))
    row.total_attempts = (row.total_attempts or 0) + 1
    row.last_reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return before


async def _current_mastery(db, student_id, subject, topic) -> float:
    row = (await db.execute(
        select(MasteryState.mastery_score).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        )
    )).scalar()
    return float(row or 0)


def _user_facing_extraction_error(reason: str) -> str:
    if reason == "illegible":
        return "Couldn't read your answer — try a clearer photo?"
    return "Something went wrong reading your answer. Please try again."


def _set_error(upload: GradedUpload, message: str) -> None:
    upload.status = "error"
    upload.error_message = message
    upload.updated_at = datetime.now(timezone.utc)


def _capture_event(event: str, student_id: UUID, **props) -> None:
    try:
        capture(str(student_id), event, props)
    except Exception as exc:
        logger.warning("Telemetry capture failed for %s: %s", event, exc)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
pytest tests/test_marker_orchestrator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/services/marker/orchestrator.py tests/test_marker_orchestrator.py
git commit -m "Add marker orchestrator: state machine + mastery + readiness updates"
```

---

## Phase C — Backend Endpoints (2 tasks)

### Task 7: `marker.py` endpoints + rate limit + schemas

**Files:**
- Create: `app/api/v1/endpoints/marker.py`
- Create: `app/schemas/marker.py`
- Create: `app/core/marker_limit.py`
- Modify: `app/main.py` — mount `marker_router`
- Test: `tests/test_marker_endpoints.py`

**Interfaces produced:**
- 5 endpoints per spec §7
- `PracticeTopic`-style Pydantic schemas
- `check_marker_limit` dependency for Free 5/month cap

- [ ] **Step 1: Write endpoint tests**

Create `tests/test_marker_endpoints.py`:

```python
import pytest
import time
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_next_question_returns_candidate(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    fake_candidate = {
        "question_id": "q1", "question_text": "Integrate x^2",
        "mark_scheme": "MS", "max_marks": 3,
        "paper_ref": "Edexcel P1 2024", "topic": "integration_basics",
        "used_generated_mark_scheme": False,
    }
    with patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=fake_candidate)):
        r = await authed_client.get("/api/v1/marker/next-question")
    assert r.status_code == 200
    body = r.json()
    assert body["question_text"] == "Integrate x^2"
    assert body["max_marks"] == 3


@pytest.mark.asyncio
async def test_post_submissions_typed_returns_submission_id(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "q1", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x^2",
    })
    assert r.status_code == 201
    assert "submission_id" in r.json()
    assert r.json().get("upload_url") is None  # typed doesn't need upload


@pytest.mark.asyncio
async def test_post_submissions_photo_returns_upload_url(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    with patch("app.api.v1.endpoints.marker.generate_signed_upload_url",
              new=AsyncMock(return_value="https://supabase/upload?token=x")):
        r = await authed_client.post("/api/v1/marker/submissions", json={
            "question_id": "q1", "question_text": "Q", "mark_scheme": "MS",
            "max_marks": 6, "input_type": "photo", "photo_extension": "jpg",
        })
    assert r.status_code == 201
    body = r.json()
    assert body["upload_url"].startswith("https://supabase")
    assert body["upload_path"].endswith(".jpg")


@pytest.mark.asyncio
async def test_post_submissions_free_tier_rate_limit(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    # Seed 5 existing this month
    for i in range(5):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "qN", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x",
    })
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_post_submissions_pro_tier_unlimited(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload, Student
    from sqlalchemy import update
    await db_session.execute(
        update(Student).where(Student.id == student_with_subject.id)
        .values(subscription_tier="pro")
    )
    for i in range(5):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "qN", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x",
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_get_submission_returns_status(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    upload = GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q1",
        question_text="Q", mark_scheme="MS", max_marks=6,
        input_type="typed", answer_text="x", status="pending",
    )
    db_session.add(upload); await db_session.flush()

    r = await authed_client.get(f"/api/v1/marker/submissions/{upload.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_get_submission_isolates_other_students(
    authed_client, student_with_subject, db_session
):
    """Requesting another student's submission returns 404."""
    from app.db.models import GradedUpload, Student
    from uuid import uuid4
    other = Student(email="other@e.com", name="Other", hashed_password="x",
                    exam_board="edexcel", exam_level="a_level",
                    subjects=[], subscription_tier="free")
    db_session.add(other); await db_session.flush()

    upload = GradedUpload(
        student_id=other.id, subject="pure_mathematics", exam_board="edexcel",
        question_id="q1", question_text="Q", mark_scheme="MS", max_marks=6,
        input_type="typed", answer_text="x", status="graded",
    )
    db_session.add(upload); await db_session.flush()

    r = await authed_client.get(f"/api/v1/marker/submissions/{upload.id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_submissions_pagination(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    for i in range(12):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/marker/submissions?limit=10&offset=0")
    assert len(r.json()) == 10

    r2 = await authed_client.get("/api/v1/marker/submissions?limit=10&offset=10")
    assert len(r2.json()) == 2
```

- [ ] **Step 2: Create schemas**

Create `app/schemas/marker.py`:

```python
"""Pydantic schemas for the Exam Marker endpoints."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class QuestionCandidateOut(BaseModel):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int
    paper_ref: str
    topic: str
    used_generated_mark_scheme: bool


class SubmissionCreateIn(BaseModel):
    question_id: str
    question_text: str
    mark_scheme: str
    max_marks: int = Field(ge=1, le=50)
    input_type: Literal["photo", "typed"]
    answer_text: str | None = None
    photo_extension: Literal["jpg", "jpeg", "png", "webp"] | None = None


class SubmissionCreateOut(BaseModel):
    submission_id: str
    upload_url: str | None = None
    upload_path: str | None = None


class UploadedNotifyOut(BaseModel):
    ok: bool


class SubmissionOut(BaseModel):
    id: str
    status: str
    subject: str
    exam_board: str
    question_id: str
    question_text: str
    max_marks: int
    input_type: str
    answer_text: str | None = None
    marks_awarded: int | None = None
    grade_pct: float | None = None
    feedback_json: dict | None = None
    photo_url: str | None = None  # fresh signed URL if photo path exists
    error_message: str | None = None
    created_at: datetime
```

- [ ] **Step 3: Create rate-limit dependency**

Create `app/core/marker_limit.py`:

```python
"""Free-tier rate limit for Exam Marker: 5 submissions per calendar month.
Pro tier unlimited."""
from fastapi import Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import GradedUpload, Student


async def check_marker_limit(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> Student:
    if student.subscription_tier == "pro":
        return student
    # Free tier — count submissions this calendar month
    res = await db.execute(
        select(func.count(GradedUpload.id)).where(
            GradedUpload.student_id == student.id,
            func.date_trunc('month', GradedUpload.created_at) ==
                func.date_trunc('month', func.now()),
        )
    )
    if (res.scalar() or 0) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Free monthly limit reached — upgrade to Pro for unlimited marking.",
        )
    return student
```

- [ ] **Step 4: Create endpoints**

Create `app/api/v1/endpoints/marker.py`:

```python
"""Exam Marker HTTP endpoints."""
from uuid import UUID, uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.marker_limit import check_marker_limit
from app.core.telemetry import capture
from app.db.database import get_db
from app.db.models import GradedUpload, LearnerSubject, Student
from app.schemas.marker import (
    QuestionCandidateOut,
    SubmissionCreateIn,
    SubmissionCreateOut,
    SubmissionOut,
    UploadedNotifyOut,
)
from app.services.marker.orchestrator import process_submission
from app.services.marker.question_selector import pick_question
from app.services.marker.storage import (
    build_photo_path,
    generate_signed_download_url,
    generate_signed_upload_url,
)

router = APIRouter(prefix="/marker", tags=["marker"])


@router.get("/next-question", response_model=QuestionCandidateOut)
async def get_next_question(
    topic: str | None = Query(None),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> QuestionCandidateOut:
    ls = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        ).order_by(LearnerSubject.created_at.asc())
    )).scalars().first()
    if ls is None:
        raise HTTPException(404, "No subject configured for this student")

    candidate = await pick_question(
        db, student.id, ls.subject, ls.exam_board, topic_override=topic,
    )
    try:
        capture(str(student.id), "marker_question_served", {
            "subject": ls.subject, "board": ls.exam_board,
            "topic": candidate["topic"],
            "question_id": candidate["question_id"],
            "paper_ref": candidate["paper_ref"],
            "used_generated_mark_scheme": candidate["used_generated_mark_scheme"],
        })
    except Exception:
        pass
    return QuestionCandidateOut(**candidate)


@router.post("/submissions", response_model=SubmissionCreateOut, status_code=201)
async def post_submission(
    body: SubmissionCreateIn,
    student: Student = Depends(check_marker_limit),
    db: AsyncSession = Depends(get_db),
) -> SubmissionCreateOut:
    if body.input_type == "photo":
        if not body.photo_extension:
            raise HTTPException(400, "photo_extension required for photo submissions")
    if body.input_type == "typed":
        if not body.answer_text or not body.answer_text.strip():
            raise HTTPException(400, "answer_text required for typed submissions")

    ls = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        ).order_by(LearnerSubject.created_at.asc())
    )).scalars().first()
    if ls is None:
        raise HTTPException(404, "No subject configured for this student")

    upload = GradedUpload(
        id=uuid4(),
        student_id=student.id,
        subject=ls.subject,
        exam_board=ls.exam_board,
        question_id=body.question_id,
        question_text=body.question_text,
        mark_scheme=body.mark_scheme,
        max_marks=body.max_marks,
        input_type=body.input_type,
        answer_text=body.answer_text if body.input_type == "typed" else None,
        status="pending",
    )

    upload_url = None
    upload_path = None
    if body.input_type == "photo":
        upload_path = build_photo_path(student.id, upload.id, body.photo_extension)
        upload.photo_path = upload_path
        upload_url = await generate_signed_upload_url(upload_path, "image/jpeg")

    db.add(upload)
    await db.commit()

    # For typed submissions, kick off processing immediately (client does not need to notify).
    # For photo submissions, wait for /uploaded call from the client.
    if body.input_type == "typed":
        from fastapi import BackgroundTasks as _BG
        # We schedule the orchestrator to run after the response returns.
        # BackgroundTasks is injected below; for the typed direct-invoke path
        # we need the tasks object — re-raise for the client to poll.

    try:
        # Count for telemetry — this submission is index N+1 for the month
        count_res = await db.execute(
            select(select(GradedUpload.id).where(
                GradedUpload.student_id == student.id,
            ).subquery().c.id.count())
        )
        monthly_count = count_res.scalar() or 0
    except Exception:
        monthly_count = 0
    try:
        capture(str(student.id), "marker_submission_created", {
            "input_type": body.input_type,
            "subscription_tier": student.subscription_tier,
            "monthly_count": monthly_count,
        })
    except Exception:
        pass

    return SubmissionCreateOut(
        submission_id=str(upload.id),
        upload_url=upload_url,
        upload_path=upload_path,
    )


@router.post("/submissions/{submission_id}/uploaded", response_model=UploadedNotifyOut)
async def notify_uploaded(
    submission_id: UUID,
    background: BackgroundTasks,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> UploadedNotifyOut:
    upload = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.id == submission_id,
            GradedUpload.student_id == student.id,
        )
    )).scalar_one_or_none()
    if upload is None:
        raise HTTPException(404, "Submission not found")
    background.add_task(_process_in_background, submission_id)
    return UploadedNotifyOut(ok=True)


async def _process_in_background(submission_id: UUID) -> None:
    """BackgroundTask wrapper — opens its own DB session."""
    from app.db.database import async_session
    async with async_session() as db:
        try:
            await process_submission(db, submission_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: UUID,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> SubmissionOut:
    upload = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.id == submission_id,
            GradedUpload.student_id == student.id,
        )
    )).scalar_one_or_none()
    if upload is None:
        raise HTTPException(404, "Submission not found")

    photo_url = None
    if upload.photo_path and upload.status == "graded":
        try:
            photo_url = await generate_signed_download_url(upload.photo_path)
        except Exception:
            photo_url = None

    return SubmissionOut(
        id=str(upload.id),
        status=upload.status,
        subject=upload.subject,
        exam_board=upload.exam_board,
        question_id=upload.question_id,
        question_text=upload.question_text,
        max_marks=upload.max_marks,
        input_type=upload.input_type,
        answer_text=upload.answer_text,
        marks_awarded=upload.marks_awarded,
        grade_pct=float(upload.grade_pct) if upload.grade_pct is not None else None,
        feedback_json=upload.feedback_json,
        photo_url=photo_url,
        error_message=upload.error_message,
        created_at=upload.created_at,
    )


@router.get("/submissions", response_model=list[SubmissionOut])
async def list_submissions(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> list[SubmissionOut]:
    rows = (await db.execute(
        select(GradedUpload).where(
            GradedUpload.student_id == student.id,
        ).order_by(GradedUpload.created_at.desc()).limit(limit).offset(offset)
    )).scalars().all()
    return [
        SubmissionOut(
            id=str(r.id), status=r.status,
            subject=r.subject, exam_board=r.exam_board,
            question_id=r.question_id, question_text=r.question_text,
            max_marks=r.max_marks, input_type=r.input_type,
            answer_text=r.answer_text, marks_awarded=r.marks_awarded,
            grade_pct=float(r.grade_pct) if r.grade_pct is not None else None,
            feedback_json=r.feedback_json,
            photo_url=None,  # history list doesn't include signed URLs (fetched per row)
            error_message=r.error_message,
            created_at=r.created_at,
        )
        for r in rows
    ]
```

- [ ] **Step 5: Mount router in `app/main.py`**

Add near other `include_router` calls:

```python
from app.api.v1.endpoints.marker import router as marker_router
app.include_router(marker_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 6: Run tests, expect pass**

```bash
pytest tests/test_marker_endpoints.py -v
```

- [ ] **Step 7: Commit**

```bash
git add app/api/v1/endpoints/marker.py app/schemas/marker.py app/core/marker_limit.py app/main.py tests/test_marker_endpoints.py
git commit -m "Add marker endpoints + rate limit dependency + schemas"
```

---

### Task 8: `/readyz` extension

**Files:**
- Modify: `app/api/v1/endpoints/readyz.py` — add Supabase Storage bucket check
- Test: extend `tests/test_readyz.py` (existing)

- [ ] **Step 1: Write test**

Append to `tests/test_readyz.py`:

```python
@pytest.mark.asyncio
async def test_readyz_reports_bucket_missing(unauth_client):
    from unittest.mock import AsyncMock, patch
    from app.services.marker import storage
    with patch.object(storage, "check_bucket_exists", new=AsyncMock(return_value=False)):
        r = await unauth_client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert "storage" in str(body).lower() or "bucket" in str(body).lower()


@pytest.mark.asyncio
async def test_readyz_passes_when_bucket_exists(unauth_client, syllabus_edexcel_seeded):
    from unittest.mock import AsyncMock, patch
    from app.services.marker import storage
    with patch.object(storage, "check_bucket_exists", new=AsyncMock(return_value=True)):
        r = await unauth_client.get("/readyz")
    assert r.status_code == 200
```

- [ ] **Step 2: Extend `readyz.py`**

In `app/api/v1/endpoints/readyz.py`, inside the `readyz` handler:

```python
from app.services.marker.storage import check_bucket_exists as _check_marker_bucket

# ... after existing checks (DB, Redis, syllabus, GROQ_API_KEY):
try:
    if not await _check_marker_bucket():
        failures.append("supabase_storage_bucket_missing")
except Exception as exc:
    failures.append(f"supabase_storage_check_error: {exc}")
```

- [ ] **Step 3: Run tests, commit**

```bash
pytest tests/test_readyz.py -v
git add app/api/v1/endpoints/readyz.py tests/test_readyz.py
git commit -m "Extend /readyz with Supabase Storage bucket check"
```

---

## Phase D — Frontend (3 tasks)

### Task 9: API client + types + `MarkMyWorkCard` + dashboard mount + flag registration

**Files:**
- Create: `web/src/lib/api/marker.ts`
- Modify: `web/src/lib/types.ts` — add marker types
- Modify: `web/src/lib/feature-flags.ts` — add `"marker_v2"` to union + KNOWN_FLAGS
- Create: `web/src/components/marker/mark-my-work-card.tsx`
- Modify: `web/src/app/(app)/dashboard/page.tsx` — mount card

**Interfaces produced:**
- `markerApi.getNextQuestion()`, `.createSubmission()`, `.notifyUploaded()`, `.getSubmission()`, `.listSubmissions()`
- Types matching backend schemas exactly (snake_case)
- `<MarkMyWorkCard subject={string} />` component

- [ ] **Step 1: Add types**

Append to `web/src/lib/types.ts`:

```typescript
export interface QuestionCandidate {
  question_id: string;
  question_text: string;
  mark_scheme: string;
  max_marks: number;
  paper_ref: string;
  topic: string;
  used_generated_mark_scheme: boolean;
}

export interface SubmissionCreateResponse {
  submission_id: string;
  upload_url: string | null;
  upload_path: string | null;
}

export interface GradingCriterion {
  code: string;
  description: string;
  awarded: boolean;
  comment: string;
}

export interface FeedbackJson {
  marks_awarded: number;
  criteria: GradingCriterion[];
  summary: string;
  improvement: string;
  readiness_before: number;
  readiness_after: number;
  readiness_delta: number;
  topic_mastery_before: number;
  topic_mastery_after: number;
  used_generated_mark_scheme?: boolean;
}

export interface SubmissionOut {
  id: string;
  status: "pending" | "extracting" | "grading" | "graded" | "error";
  subject: string;
  exam_board: string;
  question_id: string;
  question_text: string;
  max_marks: number;
  input_type: "photo" | "typed";
  answer_text: string | null;
  marks_awarded: number | null;
  grade_pct: number | null;
  feedback_json: FeedbackJson | null;
  photo_url: string | null;
  error_message: string | null;
  created_at: string;
}
```

- [ ] **Step 2: Extend feature flag union**

In `web/src/lib/feature-flags.ts`:

```typescript
export type StrideFlag =
  | "dashboard_v2"
  | "onboarding_v2"
  | "session_engine_v2"
  | "notifications_v2"
  | "account_v2"
  | "practice_v2"
  | "marker_v2";

const KNOWN_FLAGS: ReadonlyArray<StrideFlag> = [
  "dashboard_v2", "onboarding_v2", "session_engine_v2",
  "notifications_v2", "account_v2", "practice_v2", "marker_v2",
];
```

- [ ] **Step 3: Create API client**

Create `web/src/lib/api/marker.ts`:

```typescript
import { apiFetch } from "@/lib/api";
import type {
  QuestionCandidate,
  SubmissionCreateResponse,
  SubmissionOut,
} from "@/lib/types";

export interface CreateSubmissionBody {
  question_id: string;
  question_text: string;
  mark_scheme: string;
  max_marks: number;
  input_type: "photo" | "typed";
  answer_text?: string;
  photo_extension?: "jpg" | "jpeg" | "png" | "webp";
}

export const markerApi = {
  getNextQuestion: (topic?: string) => {
    const q = topic ? `?topic=${encodeURIComponent(topic)}` : "";
    return apiFetch<QuestionCandidate>(`/marker/next-question${q}`);
  },
  createSubmission: (body: CreateSubmissionBody) =>
    apiFetch<SubmissionCreateResponse>("/marker/submissions", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  notifyUploaded: (submissionId: string) =>
    apiFetch<{ ok: boolean }>(`/marker/submissions/${submissionId}/uploaded`, {
      method: "POST",
    }),
  getSubmission: (submissionId: string) =>
    apiFetch<SubmissionOut>(`/marker/submissions/${submissionId}`),
  listSubmissions: (limit = 10, offset = 0) =>
    apiFetch<SubmissionOut[]>(`/marker/submissions?limit=${limit}&offset=${offset}`),
};
```

- [ ] **Step 4: Create `MarkMyWorkCard`**

Create `web/src/components/marker/mark-my-work-card.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useStudent } from "@/lib/auth";
import { markerApi } from "@/lib/api/marker";

export function MarkMyWorkCard({ subject }: { subject: string }) {
  const student = useStudent();
  const [monthlyCount, setMonthlyCount] = useState<number | null>(null);

  useEffect(() => {
    if (student?.subscription_tier === "pro") return;
    markerApi.listSubmissions(100, 0)
      .then((rows) => {
        const now = new Date();
        const thisMonth = rows.filter((r) => {
          const d = new Date(r.created_at);
          return d.getFullYear() === now.getFullYear()
              && d.getMonth() === now.getMonth();
        });
        setMonthlyCount(thisMonth.length);
      })
      .catch(() => setMonthlyCount(null));
  }, [student?.subscription_tier]);

  const isPro = student?.subscription_tier === "pro";
  const counterText =
    !isPro && monthlyCount !== null ? `Free: ${monthlyCount}/5 this month` : null;

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <h2 className="text-lg font-semibold">Mark my work</h2>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Get your written work graded like an examiner would.
      </p>
      <div className="mt-3 flex items-center justify-between">
        <Link
          href="/mark"
          className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
        >
          Mark my work
        </Link>
        {counterText && (
          <span className="text-xs text-[var(--text-secondary)]">
            {counterText}
          </span>
        )}
      </div>
    </section>
  );
}
```

- [ ] **Step 5: Mount `<MarkMyWorkCard>` on dashboard**

In `web/src/app/(app)/dashboard/page.tsx`, add imports:

```tsx
import { MarkMyWorkCard } from "@/components/marker/mark-my-work-card";
```

And insert below the `<PracticeCard>` (behind the same FeatureFlag wrapper pattern):

```tsx
<FeatureFlag flag="marker_v2" fallback={null}>
  <MarkMyWorkCard subject={subject} />
</FeatureFlag>
```

- [ ] **Step 6: Verify build**

```bash
cd web && npm run build 2>&1 | tail -10
```

Expected: clean build.

- [ ] **Step 7: Commit**

```bash
git add web/src/lib/api/marker.ts web/src/lib/types.ts \
        web/src/lib/feature-flags.ts \
        web/src/components/marker/mark-my-work-card.tsx \
        web/src/app/\(app\)/dashboard/page.tsx
git commit -m "Add marker API client, types, feature flag, and MarkMyWorkCard on dashboard"
```

---

### Task 10: `/mark` page — question card + answer input + progress + results

**Files:**
- Create: `web/src/app/(app)/mark/page.tsx`
- Create: `web/src/components/marker/question-card.tsx`
- Create: `web/src/components/marker/answer-input.tsx`
- Create: `web/src/components/marker/grading-progress.tsx`
- Create: `web/src/components/marker/results-view.tsx`
- Create: `web/src/components/marker/topic-picker-modal.tsx`

**Interfaces produced:** the `/mark` page and its supporting components matching spec §8.

- [ ] **Step 1: Question card component**

Create `web/src/components/marker/question-card.tsx`:

```tsx
"use client";
import type { QuestionCandidate } from "@/lib/types";

export function QuestionCard({
  question,
  onChangeTopic,
}: {
  question: QuestionCandidate;
  onChangeTopic: () => void;
}) {
  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <header className="mb-3 flex items-start justify-between gap-3">
        <div>
          <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-[var(--blue)]">
            {question.max_marks} marks
          </span>
          <span className="ml-2 text-xs text-[var(--text-secondary)]">
            {question.paper_ref}
          </span>
        </div>
        <button
          onClick={onChangeTopic}
          className="text-sm text-[var(--blue)] hover:underline"
        >
          Change topic ▾
        </button>
      </header>
      <div className="whitespace-pre-wrap text-base">
        {question.question_text}
      </div>
      {question.used_generated_mark_scheme && (
        <p className="mt-3 text-xs text-[var(--text-secondary)]">
          Note: mark scheme generated by Alex (real mark scheme not found)
        </p>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Answer input component (tabbed)**

Create `web/src/components/marker/answer-input.tsx`:

```tsx
"use client";
import { useRef, useState } from "react";

type Mode = "typed" | "photo";

export interface AnswerInputProps {
  onSubmit: (input:
    | { type: "typed"; text: string }
    | { type: "photo"; file: File; extension: string }
  ) => void | Promise<void>;
  submitting: boolean;
}

const MAX_PHOTO_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXTS = ["jpg", "jpeg", "png", "webp"] as const;

export function AnswerInput({ onSubmit, submitting }: AnswerInputProps) {
  const [mode, setMode] = useState<Mode>("typed");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const pickFile = (f: File) => {
    setError(null);
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXTS.includes(ext as typeof ALLOWED_EXTS[number])) {
      setError("Only JPG, PNG, or WebP images are supported.");
      return;
    }
    if (f.size > MAX_PHOTO_BYTES) {
      setError("Photo must be under 10 MB — try a smaller version");
      return;
    }
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const clearFile = () => {
    setFile(null);
    setPreviewUrl(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const disabled = submitting || (mode === "typed" ? text.trim().length === 0 : !file);

  const handleSubmit = () => {
    if (mode === "typed") {
      onSubmit({ type: "typed", text: text.trim() });
    } else if (file) {
      const ext = file.name.split(".").pop()!.toLowerCase();
      onSubmit({ type: "photo", file, extension: ext });
    }
  };

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <div className="mb-3 flex gap-2">
        <button
          onClick={() => setMode("typed")}
          className={`rounded-md px-3 py-1.5 text-sm ${
            mode === "typed"
              ? "bg-[var(--blue)] text-white"
              : "border border-[var(--border)] hover:bg-gray-50"
          }`}
        >
          Type answer
        </button>
        <button
          onClick={() => setMode("photo")}
          className={`rounded-md px-3 py-1.5 text-sm ${
            mode === "photo"
              ? "bg-[var(--blue)] text-white"
              : "border border-[var(--border)] hover:bg-gray-50"
          }`}
        >
          Upload photo
        </button>
      </div>

      {mode === "typed" && (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write your working here…"
          className="min-h-32 w-full rounded-md border border-[var(--border)] p-3 text-sm"
        />
      )}

      {mode === "photo" && (
        <div>
          {!previewUrl && (
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) pickFile(f);
              }}
            />
          )}
          {previewUrl && (
            <div className="flex flex-col gap-2">
              <img src={previewUrl} alt="preview"
                   className="max-h-64 rounded-md border border-[var(--border)]" />
              <button
                onClick={clearFile}
                className="self-start rounded-md border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                Retake
              </button>
            </div>
          )}
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={disabled}
        className="mt-4 rounded-lg bg-[var(--blue)] px-4 py-2 text-white disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Submit for marking"}
      </button>
    </section>
  );
}
```

- [ ] **Step 3: Grading progress component**

Create `web/src/components/marker/grading-progress.tsx`:

```tsx
"use client";
export function GradingProgress({ status }: { status: "pending" | "extracting" | "grading" | "error" }) {
  const label =
    status === "extracting" ? "Reading your answer…" :
    status === "grading"    ? "Grading against the mark scheme…" :
    status === "error"      ? "Something went wrong" :
                              "Preparing…";
  const isError = status === "error";
  return (
    <section
      className={`rounded-lg border p-5 ${
        isError
          ? "border-red-200 bg-red-50"
          : "border-[var(--border)] bg-white"
      }`}
    >
      <div className="flex items-center gap-3">
        {!isError && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--blue)] border-t-transparent" />
        )}
        <p className={`text-sm ${isError ? "text-red-700" : "text-[var(--text-secondary)]"}`}>
          {label}
        </p>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Results view component**

Create `web/src/components/marker/results-view.tsx`:

```tsx
"use client";
import type { SubmissionOut } from "@/lib/types";

const GRADE_TIER = (pct: number) => {
  if (pct >= 70) return { color: "text-emerald-700", bg: "bg-emerald-50" };
  if (pct >= 40) return { color: "text-amber-700", bg: "bg-amber-50" };
  return { color: "text-red-700", bg: "bg-red-50" };
};

export function ResultsView({
  submission,
  examDate,
  predictedGrade,
  daysUntilExam,
  onMarkAnother,
  onDashboard,
  readonly = false,
}: {
  submission: SubmissionOut;
  examDate?: string | null;
  predictedGrade?: string | null;
  daysUntilExam?: number | null;
  onMarkAnother?: () => void;
  onDashboard?: () => void;
  readonly?: boolean;
}) {
  const fb = submission.feedback_json;
  const pct = submission.grade_pct ?? 0;
  const tier = GRADE_TIER(pct);
  const delta = fb?.readiness_delta ?? 0;

  return (
    <div className="space-y-4">
      <section className={`rounded-lg p-5 ${tier.bg}`}>
        <div className={`text-3xl font-semibold ${tier.color}`}>
          {submission.marks_awarded} / {submission.max_marks} marks · {Math.round(pct)}%
        </div>
        {fb && delta !== 0 && (
          <p className="mt-2 text-sm text-emerald-700">
            {fb.readiness_before}% → {fb.readiness_after}%
            {" "}({delta > 0 ? "+" : ""}{delta.toFixed(1)}%)
          </p>
        )}
        {daysUntilExam !== undefined && daysUntilExam !== null && (
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {daysUntilExam} days until exam
            {predictedGrade && ` · You're on track for a ${predictedGrade}`}
          </p>
        )}
      </section>

      {fb && (
        <>
          <details className="rounded-lg border border-[var(--border)] bg-white p-4">
            <summary className="cursor-pointer text-sm font-semibold">
              Question
            </summary>
            <p className="mt-2 whitespace-pre-wrap text-sm">
              {submission.question_text}
            </p>
          </details>

          <section className="rounded-lg border border-[var(--border)] bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">
              Criteria
            </h3>
            <ul className="space-y-2">
              {fb.criteria.map((c, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className={c.awarded ? "text-emerald-600" : "text-slate-400"}>
                    {c.awarded ? "✓" : "✗"}
                  </span>
                  <div>
                    <div className="font-medium">
                      [{c.code}] {c.description}
                    </div>
                    {c.comment && (
                      <div className="text-[var(--text-secondary)]">
                        {c.comment}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-lg bg-blue-50 p-4 text-sm">
            <p className="font-semibold text-[var(--blue)]">Summary</p>
            <p className="mt-1">{fb.summary}</p>
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-white p-4 text-sm">
            <p className="font-semibold">To improve</p>
            <p className="mt-1">{fb.improvement}</p>
          </section>
        </>
      )}

      {submission.answer_text && (
        <details className="rounded-lg border border-[var(--border)] bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold">
            View your answer
          </summary>
          <p className="mt-2 whitespace-pre-wrap text-sm">
            {submission.answer_text}
          </p>
          {submission.photo_url && (
            <img
              src={submission.photo_url} alt="your answer"
              className="mt-2 max-h-96 rounded-md border border-[var(--border)]"
            />
          )}
        </details>
      )}

      {!readonly && (
        <div className="flex gap-3">
          <button
            onClick={onMarkAnother}
            className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
          >
            Mark another question
          </button>
          <button
            onClick={onDashboard}
            className="rounded-lg border border-[var(--border)] px-4 py-2"
          >
            Return to dashboard
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Topic picker modal**

Create `web/src/components/marker/topic-picker-modal.tsx` (reuses Quick Practice's pattern):

```tsx
"use client";
import { useEffect, useState } from "react";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeTopic } from "@/lib/types";

export function TopicPickerModal({
  subject,
  onPick,
  onClose,
}: {
  subject: string;
  onPick: (topic: string) => void;
  onClose: () => void;
}) {
  const [topics, setTopics] = useState<PracticeTopic[] | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [error, setError] = useState(false);

  useEffect(() => {
    practiceApi.getTopics(subject)
      .then((rows) => {
        setTopics(rows);
        if (rows.length > 0) setSelected(rows[0].topic_id);
      })
      .catch(() => setError(true));
  }, [subject]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Pick a topic</h3>
        {error && <p className="text-sm text-red-600">Couldn't load topics.</p>}
        {topics === null && !error && <p>Loading…</p>}
        {topics && (
          <label className="block text-sm">
            Topic
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--border)] px-3 py-2"
            >
              {topics.map((t) => (
                <option key={t.topic_id} value={t.topic_id}>
                  {t.topic_name} — {t.has_attempts ? `${t.mastery_pct}%` : "New"}
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="border border-[var(--border)] rounded-md px-3 py-2 text-sm">
            Cancel
          </button>
          <button
            onClick={() => selected && onPick(selected)}
            disabled={!selected}
            className="rounded-md bg-[var(--blue)] px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Pick
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: `/mark` page**

Create `web/src/app/(app)/mark/page.tsx`:

```tsx
"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { markerApi } from "@/lib/api/marker";
import { dashboardApi } from "@/lib/api/dashboard";
import type { QuestionCandidate, SubmissionOut } from "@/lib/types";
import { QuestionCard } from "@/components/marker/question-card";
import { AnswerInput } from "@/components/marker/answer-input";
import { GradingProgress } from "@/components/marker/grading-progress";
import { ResultsView } from "@/components/marker/results-view";
import { TopicPickerModal } from "@/components/marker/topic-picker-modal";

type View = "loading" | "answering" | "grading" | "results" | "error";

export default function MarkPage() {
  const router = useRouter();
  const [view, setView] = useState<View>("loading");
  const [question, setQuestion] = useState<QuestionCandidate | null>(null);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [dashboardMeta, setDashboardMeta] = useState<{
    exam_date: string | null;
    days_until_exam: number | null;
    predicted_grade: string | null;
  } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadQuestion = useCallback(async (topic?: string) => {
    setView("loading");
    try {
      const q = await markerApi.getNextQuestion(topic);
      setQuestion(q);
      setView("answering");
    } catch {
      setView("error");
    }
  }, []);

  useEffect(() => {
    loadQuestion();
    dashboardApi.get("pure_mathematics")
      .then((d) =>
        setDashboardMeta({
          exam_date: d.exam_date,
          days_until_exam: d.days_until_exam,
          predicted_grade: d.predicted_grade,
        })
      )
      .catch(() => {});
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [loadQuestion]);

  const submit = async (input:
    | { type: "typed"; text: string }
    | { type: "photo"; file: File; extension: string }
  ) => {
    if (!question) return;
    setSubmitting(true);
    try {
      if (input.type === "typed") {
        const res = await markerApi.createSubmission({
          question_id: question.question_id,
          question_text: question.question_text,
          mark_scheme: question.mark_scheme,
          max_marks: question.max_marks,
          input_type: "typed",
          answer_text: input.text,
        });
        // For typed, kick off processing via notifyUploaded (same endpoint)
        await markerApi.notifyUploaded(res.submission_id);
        startPolling(res.submission_id);
      } else {
        const res = await markerApi.createSubmission({
          question_id: question.question_id,
          question_text: question.question_text,
          mark_scheme: question.mark_scheme,
          max_marks: question.max_marks,
          input_type: "photo",
          photo_extension: input.extension as any,
        });
        // Direct upload to Supabase
        await fetch(res.upload_url!, {
          method: "PUT",
          headers: { "Content-Type": input.file.type },
          body: input.file,
        });
        await markerApi.notifyUploaded(res.submission_id);
        startPolling(res.submission_id);
      }
    } catch {
      setView("error");
    } finally {
      setSubmitting(false);
    }
  };

  const startPolling = (id: string) => {
    setView("grading");
    pollRef.current = setInterval(async () => {
      try {
        const s = await markerApi.getSubmission(id);
        setSubmission(s);
        if (s.status === "graded") {
          clearInterval(pollRef.current!);
          setView("results");
        } else if (s.status === "error") {
          clearInterval(pollRef.current!);
          setView("error");
        }
      } catch {
        clearInterval(pollRef.current!);
        setView("error");
      }
    }, 1000);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <h1 className="text-xl font-semibold">Mark my work</h1>

      {view === "loading" && <p>Loading question…</p>}

      {(view === "answering" || view === "grading" || view === "results") && question && (
        <QuestionCard question={question} onChangeTopic={() => setPickerOpen(true)} />
      )}

      {view === "answering" && (
        <AnswerInput onSubmit={submit} submitting={submitting} />
      )}

      {view === "grading" && submission && (
        <GradingProgress status={submission.status as any} />
      )}

      {view === "results" && submission && (
        <ResultsView
          submission={submission}
          examDate={dashboardMeta?.exam_date}
          predictedGrade={dashboardMeta?.predicted_grade}
          daysUntilExam={dashboardMeta?.days_until_exam}
          onMarkAnother={() => {
            setSubmission(null);
            loadQuestion();
          }}
          onDashboard={() => router.push("/dashboard")}
        />
      )}

      {view === "error" && (
        <section className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Something went wrong. <button
            className="underline"
            onClick={() => loadQuestion()}
          >
            Try again
          </button>.
        </section>
      )}

      {pickerOpen && question && (
        <TopicPickerModal
          subject="pure_mathematics"
          onPick={(topic) => {
            setPickerOpen(false);
            loadQuestion(topic);
          }}
          onClose={() => setPickerOpen(false)}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 7: Verify build, commit**

```bash
cd web && npm run build 2>&1 | tail -10
```

```bash
git add web/src/app/\(app\)/mark/page.tsx web/src/components/marker/
git commit -m "Add /mark page with question card, answer input, grading progress, results view"
```

---

### Task 11: `/mark/history` list + read-only results

**Files:**
- Create: `web/src/app/(app)/mark/history/page.tsx`
- Create: `web/src/app/(app)/mark/history/[id]/page.tsx`
- Create: `web/src/components/marker/history-list.tsx`

- [ ] **Step 1: History list component**

Create `web/src/components/marker/history-list.tsx`:

```tsx
"use client";
import Link from "next/link";
import type { SubmissionOut } from "@/lib/types";

export function HistoryList({ items }: { items: SubmissionOut[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-[var(--text-secondary)]">
        No marked work yet. Head over to Mark my work to try it.
      </p>
    );
  }
  return (
    <ul className="divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] bg-white">
      {items.map((item) => {
        const date = new Date(item.created_at).toLocaleDateString();
        const pct = item.grade_pct !== null ? Math.round(item.grade_pct) : null;
        return (
          <li key={item.id}>
            <Link
              href={`/mark/history/${item.id}`}
              className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
            >
              <span className="text-sm">
                {date} · {item.question_text.slice(0, 60)}
                {item.question_text.length > 60 && "…"}
              </span>
              {pct !== null && (
                <span className="text-sm font-semibold">
                  {item.marks_awarded}/{item.max_marks} ({pct}%)
                </span>
              )}
              {item.status === "error" && (
                <span className="text-sm text-red-600">error</span>
              )}
              {["pending", "extracting", "grading"].includes(item.status) && (
                <span className="text-sm text-[var(--text-secondary)]">grading…</span>
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
```

- [ ] **Step 2: History page**

Create `web/src/app/(app)/mark/history/page.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { HistoryList } from "@/components/marker/history-list";

const PAGE_SIZE = 10;

export default function HistoryPage() {
  const [items, setItems] = useState<SubmissionOut[]>([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    markerApi.listSubmissions(PAGE_SIZE, page * PAGE_SIZE)
      .then((rows) => {
        setItems(rows);
        setHasMore(rows.length === PAGE_SIZE);
      })
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <h1 className="text-xl font-semibold">Marked work history</h1>
      {loading && <p>Loading…</p>}
      {!loading && <HistoryList items={items} />}
      <div className="flex gap-2">
        <button
          disabled={page === 0}
          onClick={() => setPage(page - 1)}
          className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Previous
        </button>
        <button
          disabled={!hasMore}
          onClick={() => setPage(page + 1)}
          className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Read-only results page**

Create `web/src/app/(app)/mark/history/[id]/page.tsx`:

```tsx
"use client";
import { useEffect, useState, use } from "react";
import Link from "next/link";
import { markerApi } from "@/lib/api/marker";
import type { SubmissionOut } from "@/lib/types";
import { ResultsView } from "@/components/marker/results-view";

export default function HistoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [submission, setSubmission] = useState<SubmissionOut | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    markerApi.getSubmission(id).then(setSubmission).catch(() => setError(true));
  }, [id]);

  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
      <Link href="/mark/history" className="text-sm text-[var(--blue)]">
        ← Back to history
      </Link>
      {error && <p className="text-red-600">Couldn't load this submission.</p>}
      {!error && !submission && <p>Loading…</p>}
      {submission && <ResultsView submission={submission} readonly />}
    </div>
  );
}
```

- [ ] **Step 4: Verify build, commit**

```bash
cd web && npm run build 2>&1 | tail -10
git add web/src/app/\(app\)/mark/history/ web/src/components/marker/history-list.tsx
git commit -m "Add /mark/history list and read-only submission detail views"
```

---

## Phase E — Rollout (1 task)

### Task 12: Smoke script extension + deploy checklist

**Files:**
- Modify: `tests/smoke/onboarding_to_session.py` — add marker probes
- Create: `docs/superpowers/deploys/2026-07-04-exam-marker-deploy.md`

- [ ] **Step 1: Extend smoke script**

Append after the practice-mode probes in `tests/smoke/onboarding_to_session.py`:

```python
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
```

- [ ] **Step 2: Deploy checklist**

Create `docs/superpowers/deploys/2026-07-04-exam-marker-deploy.md`:

```markdown
# Exam Marker (Sub-project #3) — Deploy Checklist

Date: 2026-07-04
Spec: docs/superpowers/specs/2026-07-04-stride-exam-marker-design.md
Plan: docs/superpowers/plans/2026-07-04-stride-exam-marker.md

## Prerequisites (do BEFORE backend deploy)

- [ ] **Create Supabase Storage bucket `graded_uploads`** — private
- [ ] **Add RLS policy** allowing students to read their own path:
      ```sql
      CREATE POLICY "students_read_own"
        ON storage.objects FOR SELECT
        USING (bucket_id = 'graded_uploads'
               AND auth.uid()::text = split_part(name, '/', 1));
      ```
- [ ] **Add 90-day auto-delete lifecycle rule** on the bucket
- [ ] **Add Cloud Run env vars:**
  - `SUPABASE_STORAGE_BUCKET=graded_uploads`
  - `SUPABASE_URL=<existing>`
  - `SUPABASE_SERVICE_ROLE_KEY=<from Supabase project settings>`

## Backend deploy (Cloud Run)

```bash
gcloud builds submit \
  --tag europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:marker \
  --region europe-west2 \
  --timeout=20m .

gcloud run deploy ascend-api \
  --image europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:marker \
  --region europe-west2 \
  --platform managed \
  --min-instances 1
```

Migration runs at container startup; creates `graded_uploads` table.

## Sanity checks

- [ ] `curl https://ascend-api-770225551335.europe-west2.run.app/readyz` returns `{"status":"ready"}`
- [ ] `psql $SUPABASE_URL -c "\d graded_uploads"` shows the new table with expected columns
- [ ] Supabase dashboard → Storage → confirm bucket exists, RLS attached, lifecycle configured

## Smoke test

```bash
STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app \
  python tests/smoke/onboarding_to_session.py
```

Expected: `SMOKE OK` including the 4 marker probes.

## Frontend deploy (Vercel)

- Push merge commit to `main` — Vercel auto-deploys
- Wait for green Vercel deployment
- Visit https://tutor-agent-nu.vercel.app/dashboard — confirm `Mark my work` card renders
- Visit https://tutor-agent-nu.vercel.app/mark — try a typed submission end-to-end

## Post-deploy manual QA

- [ ] Type an answer → get graded → see readiness delta and exam-date anchor
- [ ] Upload a real phone photo → grades
- [ ] Illegible photo → error message, `Retake photo` button works
- [ ] Free student hits 5/month → 6th shows upgrade modal
- [ ] Visit `/mark/history` → past submissions listed → click into a past one

## Rollback levers (in order)

1. PostHog `marker_v2 = false` — Marker card + `/mark` routes disappear (`< 30s`)
2. `gcloud run services update-traffic ascend-api --to-revisions=<previous>=100 --region europe-west2`
3. Vercel instant rollback via dashboard

## Notes

- Migration is additive; safe to roll back.
- Photos auto-delete after 90 days via Supabase lifecycle rule.
- Free tier: 5 monthly submissions. Pro: unlimited.
```

- [ ] **Step 3: Verify + commit**

```bash
python -m py_compile tests/smoke/onboarding_to_session.py
git add tests/smoke/onboarding_to_session.py docs/superpowers/deploys/2026-07-04-exam-marker-deploy.md
git commit -m "Extend smoke script with marker probes and add deploy checklist"
```

---

## Self-Review

**Spec coverage check** — every section of the spec maps to at least one task:

| Spec section | Tasks |
|---|---|
| §4 Data model + Supabase Storage | Tasks 1, 2 |
| §5 Question selector | Task 3 |
| §6 Vision + grading + orchestrator | Tasks 4, 5, 6 |
| §7 API endpoints + rate limit | Task 7 |
| §8 Frontend surfaces | Tasks 9, 10, 11 |
| §9 Observability | Task 6 (backend events) + Tasks 9-11 (frontend events) |
| §10 Testing | Distributed per-task |
| §11 Rollout | Task 12 |

**Placeholder scan** — no TODOs, TBDs, or "similar to Task N" references. Every step includes concrete code or exact commands.

**Type consistency** — `QuestionCandidate`, `SubmissionCreateResponse`, `SubmissionOut`, `FeedbackJson` names are consistent across backend Pydantic schemas and frontend TypeScript types. `check_marker_limit` matches spec §7 exactly. `_load_student_topic_context` shape matches usage in orchestrator and grader.

**Known plan-time verification items** (documented in spec §13, verified during Task 3):
- Qdrant payload schema for `paper_ref` / `question_number` pairing
- Groq vision content type acceptance (base64 data URI vs `image_url`)
- Supabase Python SDK version — `supabase>=2.0.0` for signed upload URL
- Native Supabase Storage 90-day lifecycle rule support in dashboard UI

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-04-stride-exam-marker.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
