# Stride UX Overhaul — Sub-project #1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Stride's chat-first UX with a dashboard-first AI exam coach shell (new onboarding wizard, dashboard with countdown + readiness + Today's Focus, Account page, segment-based session engine, in-app notifications, feature-flag kill-switches) — landing as a single deploy with all surfaces flag-gated.

**Architecture:** Approach A from spec — replace in place, with PostHog feature flags as per-surface kill-switches. Legacy components retained in codebase for one release as the off-state fallback. Single Alembic migration is additive (no DROPs) so backend rollback is safe.

**Tech Stack:** Backend = FastAPI + SQLAlchemy 2.0 (async) + Alembic + Groq LLM (3-model fallback already exists) + Upstash Redis + Qdrant. Frontend = Next.js 16 App Router + Tailwind + PostHog (already integrated for analytics; flags being added in this plan). Tests = pytest + pytest-asyncio for backend; Vitest + Testing Library where the existing frontend has tests.

**Reference spec:** `docs/superpowers/specs/2026-06-28-stride-ux-overhaul-shell-onboarding-dashboard-design.md`

## Global Constraints

- **Python:** 3.11 (Dockerfile pinned). SQLAlchemy async sessions use `app.db.database.get_db` dependency.
- **Migrations:** Alembic; runs at container startup via `start.sh`. NO DROPs in this sub-project — all changes additive. New columns must have defaults or be nullable.
- **Database:** Supabase PostgreSQL via session pooler. `asyncpg` requires `statement_cache_size=0` in connect_args (already configured).
- **Redis:** Upstash, `rediss://` URL with TLS (already configured). Use `app.core.redis_client` (existing) for new caches.
- **LLM:** Use existing `app/core/llm` 3-model fallback for any new LLM calls.
- **Auth:** JWT bearer; protected endpoints use `Depends(get_current_student)` from `app/api/v1/endpoints/auth.py`.
- **Brand palette (CSS vars in `web/src/app/globals.css`):** Primary `#0F172A`, Slate `#1E293B`, Emerald accent `#10B981` (CSS var named `--blue` for legacy reasons — do not rename), Bright Emerald `#34D399`, Off-white bg `#F8FAFC`, Border `#E2E8F0`, Secondary text `#64748B`.
- **Subjects/boards live at launch:** Pure Mathematics × Edexcel 9MA0 + Pure Mathematics × Cambridge 9709. Others render with `Coming soon` tag and disabled state; backend defensively rejects unsupported combos.
- **Syllabus version pinned at launch:** `2026.1`.
- **Free tier rate limit:** 50 messages/day (current demo override). Existing `FREE_DAILY_MESSAGE_LIMIT` env var.
- **Feature flag client:** PostHog feature flags. Defaults `true` for all surfaces; flags exist as kill-switches.
- **Commit style:** match existing repo — short sentence-case subject, no Co-Authored-By footer (existing repo convention).
- **Deploy targets:** Backend → Cloud Run (`gcloud builds submit` + `gcloud run deploy`), europe-west2, GCP project `ascend-tutor-prod`, Cloud Run service `ascend-api`. Frontend → Vercel auto-deploy from `main`, Root Directory `web/`.
- **CLAUDE.md in repo root:** project requires plan → task → execution → verification flow; this plan IS the planning artifact, so per-task verification stays as part of each task's "test passes" gate.

## File Structure

### Backend — new files

| Path | Responsibility |
|---|---|
| `app/services/learner_profile_service.py` | CRUD for `learner_subjects` (incl. draft management), preferences updates |
| `app/services/readiness_service.py` | Readiness % calc, snapshot write, trend computation |
| `app/services/notification_service.py` | `emit_notification`, list, mark-read |
| `app/services/today_focus_service.py` | Shape selector + slot fillers + Redis cache + persistence to `today_focus_history` |
| `app/agents/handlers/__init__.py` | Handler registry |
| `app/agents/handlers/base.py` | `SegmentHandler` protocol + shared types |
| `app/agents/handlers/diagnostic.py` | `diagnostic_question` handler |
| `app/agents/handlers/practice.py` | `practice` handler (refactor of existing flow) |
| `app/agents/handlers/review.py` | `review` handler |
| `app/agents/handlers/mistakes.py` | `mistakes` handler |
| `app/agents/orchestrator.py` | Segment transition logic, v1↔v2 session shim |
| `app/api/v1/endpoints/onboarding.py` | Wizard state + per-step submit endpoints |
| `app/api/v1/endpoints/dashboard.py` | Dashboard payload endpoint |
| `app/api/v1/endpoints/account.py` | Profile / subjects / preferences updates |
| `app/api/v1/endpoints/notifications.py` | List + mark-read |
| `app/api/v1/endpoints/readyz.py` | `/readyz` readiness probe (separate from existing `/healthz`) |
| `app/core/syllabus_seed.py` | Pure Maths × Edexcel/Cambridge topic lists for version 2026.1 |
| `app/core/grade_prediction.py` | Readiness-%-to-grade bucketing |
| `app/core/feature_flags.py` | PostHog feature-flag server client + cache |
| `app/schemas/onboarding.py` | Pydantic schemas for onboarding endpoints |
| `app/schemas/dashboard.py` | Pydantic schemas for dashboard payload |
| `app/schemas/account.py` | Pydantic schemas for account endpoints |
| `app/schemas/notifications.py` | Pydantic schemas for notifications |
| `alembic/versions/<rev>_ux_overhaul_v1.py` | Migration: new tables + columns + backfill + syllabus seed |
| `tests/fixtures/pre_migration_v2.sql` | Snapshot of pre-migration data shape for regression tests |
| `tests/test_migration_regression.py` | Migration regression suite |
| `tests/test_readiness_service.py` | Unit tests for readiness service |
| `tests/test_today_focus_service.py` | Unit tests for shape selector + slot fillers |
| `tests/test_segment_handlers.py` | Unit tests per handler |
| `tests/test_onboarding_endpoints.py` | Integration tests for wizard flow |
| `tests/test_dashboard_endpoint.py` | Integration tests for dashboard payload |
| `tests/test_notification_service.py` | Unit tests for notifications |
| `tests/smoke/onboarding_to_session.py` | Post-deploy smoke script |

### Backend — modified files

| Path | Change |
|---|---|
| `app/db/models.py` | Add 5 new model classes (`LearnerSubject`, `SyllabusTopic`, `ReadinessSnapshot`, `Notification`, `TodayFocusHistory`); add columns to `Student` (`preferences`, `onboarded_at`, `is_admin`) and `TutorSession` (`session_type`, `session_version`, `segment_plan`, `current_segment_idx`) |
| `app/workflows/state.py` | Add `session_version`, `segment_plan`, `current_segment_idx`, `segment_progress` fields to `SessionState` |
| `app/services/session_service.py` | Route streaming/start through orchestrator; remove phase-advance logic (now handler-internal) |
| `app/agents/tutor_agent.py` | Extract reusable system-prompt builder; add preference injection block |
| `app/api/v1/endpoints/sessions.py` | Adjust `/sessions/start` payload (session_type, segment_plan); add segment-state fields to GET responses |
| `app/api/v1/endpoints/admin.py` | Add `/admin/students/{id}/inspect` |
| `app/api/v1/endpoints/auth.py` | Extend `me` response with `is_admin`; gate admin endpoints |
| `app/main.py` | Mount new routers (onboarding, dashboard, account, notifications, readyz) |
| `start.sh` | Confirm Alembic runs before uvicorn (existing — verify only) |

### Frontend — new files

| Path | Responsibility |
|---|---|
| `web/src/app/(app)/account/page.tsx` | Account page with anchored sections |
| `web/src/app/(admin)/admin/students/[id]/page.tsx` | Admin inspect (read-only JSON) |
| `web/src/app/(admin)/layout.tsx` | Admin route group layout (gates on `is_admin`) |
| `web/src/app/(onboarding)/onboarding/education-system/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/subjects/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/exam-board/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/exam-date/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/target-grade/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/assessment/page.tsx` | Wizard step (diagnostic launcher) |
| `web/src/app/(onboarding)/onboarding/preferences/page.tsx` | Wizard step |
| `web/src/app/(onboarding)/onboarding/roadmap/page.tsx` | Final reveal |
| `web/src/components/shell/top-bar.tsx` | Logo + notification bell + avatar menu |
| `web/src/components/shell/notification-bell.tsx` | Bell icon + dropdown panel |
| `web/src/components/shell/avatar-menu.tsx` | Account / Sign out menu |
| `web/src/components/shell/feature-flag.tsx` | `<FeatureFlag flag="...">` wrapper |
| `web/src/components/onboarding/wizard-shell.tsx` | Progress chrome + back/next chrome shared across steps |
| `web/src/components/onboarding/fields/system-picker.tsx` | Education system selector |
| `web/src/components/onboarding/fields/subject-picker.tsx` | Subject multi-select with Coming Soon |
| `web/src/components/onboarding/fields/board-picker.tsx` | Per-subject board selector |
| `web/src/components/onboarding/fields/exam-date-picker.tsx` | Date input + "Don't know yet" |
| `web/src/components/onboarding/fields/grade-picker.tsx` | A*-E selector |
| `web/src/components/dashboard/countdown-band.tsx` | Days remaining + target grade + prediction |
| `web/src/components/dashboard/readiness-card.tsx` | Large % + progress bar + trend |
| `web/src/components/dashboard/resume-session-card.tsx` | Resume affordance |
| `web/src/components/dashboard/today-focus-card.tsx` | Progress dots + 3 segments + Start CTA |
| `web/src/components/dashboard/recent-activity.tsx` | Last studied / streak-break line |
| `web/src/components/dashboard/topics-list.tsx` | Strong / weak lists |
| `web/src/components/dashboard/subject-switcher.tsx` | Header subject dropdown |
| `web/src/components/account/subject-card.tsx` | Enriched per-subject card |
| `web/src/components/account/edit-subject-modal.tsx` | Reuses wizard fields |
| `web/src/components/account/preferences-section.tsx` | Learning preferences |
| `web/src/components/account/billing-section.tsx` | Free vs Pro variants |
| `web/src/components/session/exit-confirmation.tsx` | Smart leave modal |
| `web/src/components/session/segment-progress.tsx` | Dots row in session view |
| `web/src/lib/api/onboarding.ts` | API client for wizard endpoints |
| `web/src/lib/api/dashboard.ts` | API client for dashboard payload |
| `web/src/lib/api/account.ts` | API client for account endpoints |
| `web/src/lib/api/notifications.ts` | API client for notifications |
| `web/src/lib/feature-flags.ts` | PostHog feature-flag React hooks |

### Frontend — modified files

| Path | Change |
|---|---|
| `web/src/app/(app)/layout.tsx` | New shell: top bar with bell + avatar; remove old nav |
| `web/src/app/(app)/dashboard/page.tsx` | Rewrite per Section 6 of spec |
| `web/src/app/(app)/session/[id]/page.tsx` | Full-screen takeover; segment progress; smart exit |
| `web/src/app/(app)/progress/page.tsx` | Delete contents; replace with 410 redirect to `/dashboard` |
| `web/src/app/(onboarding)/onboarding/page.tsx` | Redirect to `/onboarding/welcome` |
| `web/src/app/(onboarding)/onboarding/welcome/page.tsx` | Rewrite as wizard step #1 |
| `web/src/app/(onboarding)/onboarding/layout.tsx` | Wizard chrome (uses `wizard-shell`) |
| `web/src/lib/types.ts` | New types matching backend Pydantic schemas |
| `web/src/lib/api.ts` | Add helper for PostHog flag fetching (or move to feature-flags.ts) |

---

## Phase A — Data Layer (3 tasks)

### Task 1: Add new SQLAlchemy models + extend existing models

**Files:**
- Modify: `app/db/models.py`
- Test: `tests/test_models_smoke.py` (create)

**Interfaces produced (used by later tasks):**
- `LearnerSubject` ORM model with fields per spec §4
- `SyllabusTopic` ORM model
- `ReadinessSnapshot` ORM model
- `Notification` ORM model
- `TodayFocusHistory` ORM model
- `Student.preferences: Mapped[dict]`, `Student.onboarded_at: Mapped[datetime | None]`, `Student.is_admin: Mapped[bool]`
- `TutorSession.session_type: Mapped[str]`, `TutorSession.session_version: Mapped[int]`, `TutorSession.segment_plan: Mapped[list]`, `TutorSession.current_segment_idx: Mapped[int]`

- [ ] **Step 1: Write smoke test asserting models import and basic columns exist**

```python
# tests/test_models_smoke.py
from app.db.models import (
    Student, TutorSession, LearnerSubject, SyllabusTopic,
    ReadinessSnapshot, Notification, TodayFocusHistory,
)

def test_new_models_importable():
    for cls in (LearnerSubject, SyllabusTopic, ReadinessSnapshot,
                Notification, TodayFocusHistory):
        assert hasattr(cls, "__tablename__")

def test_student_has_new_columns():
    assert "preferences" in Student.__table__.columns
    assert "onboarded_at" in Student.__table__.columns
    assert "is_admin" in Student.__table__.columns

def test_session_has_segment_columns():
    cols = TutorSession.__table__.columns
    for name in ("session_type", "session_version", "segment_plan", "current_segment_idx"):
        assert name in cols
```

- [ ] **Step 2: Run test, expect import errors / missing column errors**

Run: `pytest tests/test_models_smoke.py -v`
Expected: FAIL — new model classes don't exist.

- [ ] **Step 3: Add new model classes to `app/db/models.py`**

Append after existing `PasswordResetToken`:

```python
class LearnerSubject(Base):
    __tablename__ = "learner_subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_level: Mapped[str] = mapped_column(String(20), nullable=False, default="a_level")
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_grade: Mapped[str] = mapped_column(String(2), nullable=False)
    current_grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    syllabus_version: Mapped[str] = mapped_column(String(20), nullable=False, default="2026.1")
    recommended_minutes_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject", name="uq_learner_subjects_student_subject"),)


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_board: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_topic_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("exam_board", "subject", "version", "topic_id",
                                       name="uq_syllabus_board_subject_version_topic"),)


class ReadinessSnapshot(Base):
    __tablename__ = "readiness_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    readiness_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject", "snapshot_date",
                                       name="uq_readiness_student_subject_date"),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TodayFocusHistory(Base):
    __tablename__ = "today_focus_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    focus_date: Mapped[date] = mapped_column(Date, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(20), nullable=False)
    shape: Mapped[str] = mapped_column(String(50), nullable=False)
    segment_plan: Mapped[list] = mapped_column(JSON, nullable=False)
    reasoning: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "subject", "focus_date",
                                       name="uq_today_focus_student_subject_date"),)
```

Add to the top of the file's imports: `from sqlalchemy import UniqueConstraint`.

- [ ] **Step 4: Add new columns to `Student` and `TutorSession`**

In `Student` (after `created_at`):
```python
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

In `TutorSession` (after `mode`):
```python
    session_type: Mapped[str] = mapped_column(String(20), default="practice", nullable=False)
    session_version: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    segment_plan: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    current_segment_idx: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```

- [ ] **Step 5: Run smoke tests, expect pass**

Run: `pytest tests/test_models_smoke.py -v`
Expected: PASS (all three tests).

- [ ] **Step 6: Commit**

```bash
git add app/db/models.py tests/test_models_smoke.py
git commit -m "Add ORM models for UX overhaul (learner_subjects, syllabus, snapshots, notifications, today_focus_history)"
```

---

### Task 2: Alembic migration with backfill + syllabus seed

**Files:**
- Create: `alembic/versions/<auto>_ux_overhaul_v1.py` (use `alembic revision -m`)
- Create: `app/core/syllabus_seed.py`

**Interfaces produced:**
- Migration revision name `ux_overhaul_v1` (referenced by regression tests)
- `app.core.syllabus_seed.EDEXCEL_9MA0_TOPICS: list[dict]` and `CAMBRIDGE_9709_TOPICS: list[dict]` — each item `{topic_id, topic_name, parent_topic_id, ordinal}`

- [ ] **Step 1: Define syllabus seed data**

Create `app/core/syllabus_seed.py`:

```python
"""Pure Mathematics syllabus topic lists for version 2026.1.

Source: Edexcel 9MA0 spec + Cambridge 9709 syllabus, distilled to topic IDs
the engine uses for mastery tracking + readiness calculation.
"""

SYLLABUS_VERSION = "2026.1"

EDEXCEL_9MA0_TOPICS: list[dict] = [
    {"topic_id": "algebra_indices_surds", "topic_name": "Algebra: indices and surds", "parent_topic_id": None, "ordinal": 1},
    {"topic_id": "algebra_quadratics", "topic_name": "Quadratics", "parent_topic_id": None, "ordinal": 2},
    {"topic_id": "algebra_inequalities", "topic_name": "Inequalities", "parent_topic_id": None, "ordinal": 3},
    {"topic_id": "algebra_polynomials", "topic_name": "Polynomials", "parent_topic_id": None, "ordinal": 4},
    {"topic_id": "algebra_graphs_transformations", "topic_name": "Graphs and transformations", "parent_topic_id": None, "ordinal": 5},
    {"topic_id": "coordinate_geometry_straight_lines", "topic_name": "Straight lines", "parent_topic_id": None, "ordinal": 6},
    {"topic_id": "coordinate_geometry_circles", "topic_name": "Circles", "parent_topic_id": None, "ordinal": 7},
    {"topic_id": "trigonometry_ratios", "topic_name": "Trigonometric ratios and identities", "parent_topic_id": None, "ordinal": 8},
    {"topic_id": "trigonometry_equations", "topic_name": "Trigonometric equations", "parent_topic_id": None, "ordinal": 9},
    {"topic_id": "exponentials_logarithms", "topic_name": "Exponentials and logarithms", "parent_topic_id": None, "ordinal": 10},
    {"topic_id": "differentiation_basics", "topic_name": "Differentiation: first principles and rules", "parent_topic_id": None, "ordinal": 11},
    {"topic_id": "differentiation_applications", "topic_name": "Differentiation applications (tangents, stationary points)", "parent_topic_id": None, "ordinal": 12},
    {"topic_id": "differentiation_chain_product_quotient", "topic_name": "Chain, product, quotient rules", "parent_topic_id": None, "ordinal": 13},
    {"topic_id": "integration_basics", "topic_name": "Integration: indefinite and definite", "parent_topic_id": None, "ordinal": 14},
    {"topic_id": "integration_substitution_parts", "topic_name": "Integration by substitution and by parts", "parent_topic_id": None, "ordinal": 15},
    {"topic_id": "integration_area", "topic_name": "Integration: area under curve", "parent_topic_id": None, "ordinal": 16},
    {"topic_id": "sequences_series", "topic_name": "Sequences and series", "parent_topic_id": None, "ordinal": 17},
    {"topic_id": "binomial_expansion", "topic_name": "Binomial expansion", "parent_topic_id": None, "ordinal": 18},
    {"topic_id": "functions", "topic_name": "Functions and inverse functions", "parent_topic_id": None, "ordinal": 19},
    {"topic_id": "vectors_2d_3d", "topic_name": "Vectors (2D and 3D)", "parent_topic_id": None, "ordinal": 20},
    {"topic_id": "numerical_methods", "topic_name": "Numerical methods", "parent_topic_id": None, "ordinal": 21},
    {"topic_id": "proof", "topic_name": "Proof (direct, contradiction, induction)", "parent_topic_id": None, "ordinal": 22},
]

CAMBRIDGE_9709_TOPICS: list[dict] = [
    {"topic_id": "algebra_quadratics", "topic_name": "Quadratics", "parent_topic_id": None, "ordinal": 1},
    {"topic_id": "algebra_functions", "topic_name": "Functions", "parent_topic_id": None, "ordinal": 2},
    {"topic_id": "coordinate_geometry", "topic_name": "Coordinate geometry", "parent_topic_id": None, "ordinal": 3},
    {"topic_id": "circular_measure", "topic_name": "Circular measure (radians)", "parent_topic_id": None, "ordinal": 4},
    {"topic_id": "trigonometry", "topic_name": "Trigonometry", "parent_topic_id": None, "ordinal": 5},
    {"topic_id": "series_binomial", "topic_name": "Series and binomial expansion", "parent_topic_id": None, "ordinal": 6},
    {"topic_id": "differentiation", "topic_name": "Differentiation", "parent_topic_id": None, "ordinal": 7},
    {"topic_id": "integration", "topic_name": "Integration", "parent_topic_id": None, "ordinal": 8},
    {"topic_id": "algebra_polynomials_partial_fractions", "topic_name": "Polynomials and partial fractions", "parent_topic_id": None, "ordinal": 9},
    {"topic_id": "logarithmic_exponential", "topic_name": "Logarithmic and exponential functions", "parent_topic_id": None, "ordinal": 10},
    {"topic_id": "trigonometry_advanced", "topic_name": "Trigonometry (advanced)", "parent_topic_id": None, "ordinal": 11},
    {"topic_id": "differentiation_advanced", "topic_name": "Differentiation (advanced rules + implicit + parametric)", "parent_topic_id": None, "ordinal": 12},
    {"topic_id": "integration_advanced", "topic_name": "Integration (advanced techniques)", "parent_topic_id": None, "ordinal": 13},
    {"topic_id": "numerical_solution_equations", "topic_name": "Numerical solution of equations", "parent_topic_id": None, "ordinal": 14},
    {"topic_id": "vectors", "topic_name": "Vectors", "parent_topic_id": None, "ordinal": 15},
    {"topic_id": "differential_equations", "topic_name": "Differential equations", "parent_topic_id": None, "ordinal": 16},
    {"topic_id": "complex_numbers", "topic_name": "Complex numbers", "parent_topic_id": None, "ordinal": 17},
]
```

These lists are the authoritative seed for sub-project #1. They can be revised at plan-time after confirming against the current `study_plan_service` topic list, but ship as written if no conflict.

- [ ] **Step 2: Generate migration scaffold**

```bash
source venv/bin/activate
alembic revision -m "ux_overhaul_v1"
```

This creates `alembic/versions/<rev>_ux_overhaul_v1.py`. Record the `<rev>` hash.

- [ ] **Step 3: Implement migration upgrade()**

Replace the generated file's contents (preserving the `revision` and `down_revision` lines Alembic generated):

```python
"""ux_overhaul_v1

Revision ID: <generated>
Revises: <previous>
Create Date: 2026-06-28

Adds tables and columns for the UX overhaul sub-project #1:
- learner_subjects, syllabus_topics, readiness_snapshots, notifications, today_focus_history
- students.preferences, onboarded_at, is_admin
- sessions.session_type, session_version, segment_plan, current_segment_idx
Backfills learner_subjects from existing Student flat fields.
Seeds syllabus_topics for Pure Maths × Edexcel 9MA0 and Cambridge 9709 (version 2026.1).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS, CAMBRIDGE_9709_TOPICS, SYLLABUS_VERSION

revision = "<keep generated>"
down_revision = "<keep generated>"
branch_labels = None
depends_on = None


def upgrade():
    # ---- learner_subjects ----
    op.create_table(
        "learner_subjects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("exam_level", sa.String(20), nullable=False, server_default="a_level"),
        sa.Column("exam_date", sa.Date, nullable=True),
        sa.Column("target_grade", sa.String(2), nullable=False, server_default="A"),
        sa.Column("current_grade", sa.String(2), nullable=True),
        sa.Column("syllabus_version", sa.String(20), nullable=False, server_default=SYLLABUS_VERSION),
        sa.Column("recommended_minutes_per_day", sa.Integer, nullable=True),
        sa.Column("is_draft", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "subject", name="uq_learner_subjects_student_subject"),
    )

    # ---- syllabus_topics ----
    op.create_table(
        "syllabus_topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(100), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("parent_topic_id", sa.String(100), nullable=True),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("exam_board", "subject", "version", "topic_id",
                            name="uq_syllabus_board_subject_version_topic"),
    )

    # ---- readiness_snapshots ----
    op.create_table(
        "readiness_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("readiness_pct", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "subject", "snapshot_date",
                            name="uq_readiness_student_subject_date"),
    )

    # ---- notifications ----
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_student_read_created",
                    "notifications", ["student_id", "read_at", sa.text("created_at DESC")])

    # ---- today_focus_history ----
    op.create_table(
        "today_focus_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("focus_date", sa.Date, nullable=False),
        sa.Column("generator_version", sa.String(20), nullable=False),
        sa.Column("shape", sa.String(50), nullable=False),
        sa.Column("segment_plan", JSONB, nullable=False),
        sa.Column("reasoning", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "subject", "focus_date",
                            name="uq_today_focus_student_subject_date"),
    )

    # ---- students new columns ----
    op.add_column("students", sa.Column("preferences", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("students", sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("students", sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("false")))

    # ---- sessions new columns ----
    op.add_column("sessions", sa.Column("session_type", sa.String(20), nullable=False, server_default="practice"))
    op.add_column("sessions", sa.Column("session_version", sa.Integer, nullable=False, server_default="2"))
    op.add_column("sessions", sa.Column("segment_plan", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("sessions", sa.Column("current_segment_idx", sa.Integer, nullable=False, server_default="0"))

    # ---- backfill: legacy sessions -> v1 ----
    op.execute("UPDATE sessions SET session_version = 1 WHERE created_at < NOW()")

    # ---- backfill: learner_subjects from existing Student flat fields ----
    op.execute("""
        INSERT INTO learner_subjects
            (id, student_id, subject, exam_board, exam_level, exam_date,
             target_grade, syllabus_version, is_draft)
        SELECT
            gen_random_uuid(),
            s.id,
            jsonb_array_elements_text(
                CASE WHEN jsonb_typeof(to_jsonb(s.subjects)) = 'array'
                     THEN to_jsonb(s.subjects)
                     ELSE '[]'::jsonb END
            ) AS subject,
            COALESCE(s.exam_board, 'edexcel'),
            COALESCE(s.exam_level, 'a_level'),
            s.exam_date,
            'A',
            '2026.1',
            false  -- not drafts; existing students are real
        FROM students s
        WHERE s.onboarding_complete = true
          AND s.subjects IS NOT NULL
          AND jsonb_typeof(to_jsonb(s.subjects)) = 'array'
        ON CONFLICT (student_id, subject) DO NOTHING
    """)

    # ---- seed syllabus_topics ----
    syllabus_rows = []
    for t in EDEXCEL_9MA0_TOPICS:
        syllabus_rows.append({
            "exam_board": "edexcel", "subject": "pure_mathematics",
            "version": SYLLABUS_VERSION, **t,
        })
    for t in CAMBRIDGE_9709_TOPICS:
        syllabus_rows.append({
            "exam_board": "cambridge", "subject": "pure_mathematics",
            "version": SYLLABUS_VERSION, **t,
        })
    op.bulk_insert(
        sa.table("syllabus_topics",
                 sa.column("exam_board", sa.String),
                 sa.column("subject", sa.String),
                 sa.column("version", sa.String),
                 sa.column("topic_id", sa.String),
                 sa.column("topic_name", sa.String),
                 sa.column("parent_topic_id", sa.String),
                 sa.column("ordinal", sa.Integer)),
        syllabus_rows,
    )


def downgrade():
    # Additive migration; downgrade drops only the new objects.
    op.drop_column("sessions", "current_segment_idx")
    op.drop_column("sessions", "segment_plan")
    op.drop_column("sessions", "session_version")
    op.drop_column("sessions", "session_type")
    op.drop_column("students", "is_admin")
    op.drop_column("students", "onboarded_at")
    op.drop_column("students", "preferences")
    op.drop_table("today_focus_history")
    op.drop_index("ix_notifications_student_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("readiness_snapshots")
    op.drop_table("syllabus_topics")
    op.drop_table("learner_subjects")
```

- [ ] **Step 4: Apply migration against a fresh dev DB**

```bash
# Use SYNC_DATABASE_URL pointing to a fresh local Postgres for this test.
alembic upgrade head
```

Expected: completes without error. Run `psql $SYNC_DATABASE_URL -c "\dt"` and verify all 5 new tables exist.

- [ ] **Step 5: Verify syllabus seed**

```bash
psql $SYNC_DATABASE_URL -c "SELECT exam_board, count(*) FROM syllabus_topics GROUP BY exam_board;"
```

Expected output:
```
 exam_board | count
------------+-------
 edexcel    |    22
 cambridge  |    17
```

- [ ] **Step 6: Commit**

```bash
git add app/core/syllabus_seed.py alembic/versions/*_ux_overhaul_v1.py
git commit -m "Add ux_overhaul_v1 migration: new tables, backfill, syllabus seed"
```

---

### Task 3: Migration regression test suite

**Files:**
- Create: `tests/fixtures/pre_migration_v2.sql`
- Create: `tests/test_migration_regression.py`
- Create: `tests/conftest.py` extensions (only if missing — check first; existing `conftest.py` may already have db fixtures)

**Interfaces produced:**
- pytest fixture `legacy_db` that loads `pre_migration_v2.sql` before running the migration

- [ ] **Step 1: Create pre-migration fixture SQL**

Create `tests/fixtures/pre_migration_v2.sql`:

```sql
-- Snapshot of representative pre-migration data shape.
-- Loaded BEFORE the ux_overhaul_v1 migration runs in regression tests.
-- Mirrors the state of production at deploy time.

-- A student who completed legacy onboarding with one subject
INSERT INTO students (id, email, name, hashed_password, exam_board, exam_level, subjects, exam_date, onboarding_complete, subscription_tier, created_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'alice@example.com', 'Alice',
    'bcrypt$dummy',
    'edexcel', 'a_level', '["pure_mathematics"]'::json,
    '2026-11-15', true, 'free', NOW() - INTERVAL '30 days'
);

-- A student mid-onboarding (no subjects yet)
INSERT INTO students (id, email, name, hashed_password, exam_board, exam_level, subjects, onboarding_complete, subscription_tier, created_at)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'bob@example.com', 'Bob',
    'bcrypt$dummy',
    'cambridge', 'a_level', '[]'::json,
    false, 'free', NOW() - INTERVAL '1 day'
);

-- Alice has an in-flight session
INSERT INTO sessions (id, student_id, subject, topic, mode, messages, started_at)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'pure_mathematics', 'integration_basics', 'explain',
    '[{"role":"tutor","content":"Hi"}]'::json,
    NOW() - INTERVAL '1 hour'
);

-- Alice has mastery rows
INSERT INTO mastery_state (id, student_id, subject, topic, mastery_score, total_attempts, correct_streak)
VALUES
    ('44444444-4444-4444-4444-444444444441', '11111111-1111-1111-1111-111111111111',
     'pure_mathematics', 'integration_basics', 0.65, 5, 2),
    ('44444444-4444-4444-4444-444444444442', '11111111-1111-1111-1111-111111111111',
     'pure_mathematics', 'differentiation_basics', 0.82, 8, 4);
```

- [ ] **Step 2: Write regression tests**

Create `tests/test_migration_regression.py`:

```python
"""Migration regression tests for ux_overhaul_v1.

Loads a representative snapshot of pre-migration data, runs the migration,
and verifies no data loss or schema regression.
"""
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text


FIXTURE = Path(__file__).parent / "fixtures" / "pre_migration_v2.sql"


@pytest.fixture
def legacy_db():
    """Provision an empty DB at the previous Alembic revision, load fixture data, yield URL."""
    url = os.environ["TEST_SYNC_DATABASE_URL"]
    engine = create_engine(url)
    # Stamp down one revision so we can re-run the new migration
    subprocess.check_call(["alembic", "downgrade", "-1"], env={**os.environ, "SYNC_DATABASE_URL": url})
    # Load fixture
    with engine.begin() as conn:
        for stmt in FIXTURE.read_text().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    yield url
    # Cleanup: alembic upgrade restored by caller


def test_migration_backfills_learner_subjects(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT subject, exam_board, exam_date FROM learner_subjects "
            "WHERE student_id = '11111111-1111-1111-1111-111111111111'"
        )).fetchall()
    assert len(rows) == 1
    assert rows[0].subject == "pure_mathematics"
    assert rows[0].exam_board == "edexcel"
    assert str(rows[0].exam_date) == "2026-11-15"


def test_migration_skips_mid_onboarding_users(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        count = conn.execute(text(
            "SELECT count(*) FROM learner_subjects "
            "WHERE student_id = '22222222-2222-2222-2222-222222222222'"
        )).scalar()
    assert count == 0  # Bob's empty subjects array → no backfill row


def test_migration_marks_existing_sessions_as_v1(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT session_version, session_type, current_segment_idx "
            "FROM sessions WHERE id = '33333333-3333-3333-3333-333333333333'"
        )).fetchone()
    assert row.session_version == 1
    assert row.session_type == "practice"
    assert row.current_segment_idx == 0


def test_migration_preserves_mastery_rows(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT topic, mastery_score FROM mastery_state "
            "WHERE student_id = '11111111-1111-1111-1111-111111111111' "
            "ORDER BY topic"
        )).fetchall()
    assert len(rows) == 2
    assert rows[0].topic == "differentiation_basics"
    assert rows[0].mastery_score == pytest.approx(0.82)
    assert rows[1].topic == "integration_basics"
    assert rows[1].mastery_score == pytest.approx(0.65)


def test_migration_seeds_syllabus_topics(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        edx = conn.execute(text(
            "SELECT count(*) FROM syllabus_topics "
            "WHERE exam_board='edexcel' AND version='2026.1'"
        )).scalar()
        cam = conn.execute(text(
            "SELECT count(*) FROM syllabus_topics "
            "WHERE exam_board='cambridge' AND version='2026.1'"
        )).scalar()
    assert edx == 22
    assert cam == 17


def test_migration_preferences_default_empty_dict(legacy_db):
    subprocess.check_call(["alembic", "upgrade", "head"])
    engine = create_engine(legacy_db)
    with engine.connect() as conn:
        prefs = conn.execute(text(
            "SELECT preferences FROM students "
            "WHERE id = '11111111-1111-1111-1111-111111111111'"
        )).scalar()
    assert prefs == {}
```

- [ ] **Step 3: Run regression tests**

```bash
# Requires TEST_SYNC_DATABASE_URL env var pointing to an isolated test DB.
TEST_SYNC_DATABASE_URL=postgresql://localhost/stride_test \
  pytest tests/test_migration_regression.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/pre_migration_v2.sql tests/test_migration_regression.py
git commit -m "Add migration regression tests for ux_overhaul_v1"
```

---

## Phase B — Backend Services (4 tasks)

### Task 4: `learner_profile_service`

**Files:**
- Create: `app/services/learner_profile_service.py`
- Create: `tests/test_learner_profile_service.py`

**Interfaces produced:**
- `async def get_or_create_draft(db, student_id) -> list[LearnerSubject]`
- `async def upsert_subject_draft(db, student_id, subject, **fields) -> LearnerSubject`
- `async def list_subjects(db, student_id, include_drafts=False) -> list[LearnerSubject]`
- `async def finalize_drafts(db, student_id) -> int` (flips is_draft=false, sets Student.onboarded_at + onboarding_complete=true; returns count flipped)
- `async def update_subject(db, student_id, subject_id, **fields) -> LearnerSubject`
- `async def update_preferences(db, student_id, prefs: dict) -> Student`
- `def is_supported_combo(subject: str, board: str, level: str) -> bool`

**Validation:** `SUPPORTED_COMBOS = {("pure_mathematics", "edexcel", "a_level"), ("pure_mathematics", "cambridge", "a_level")}`. Backend defensively rejects others with HTTPException(400) at the endpoint layer.

- [ ] **Step 1: Write tests covering draft lifecycle**

```python
# tests/test_learner_profile_service.py
import pytest
from app.services import learner_profile_service as svc

@pytest.mark.asyncio
async def test_upsert_creates_draft(db_session, student):
    s = await svc.upsert_subject_draft(db_session, student.id,
                                       subject="pure_mathematics",
                                       exam_board="edexcel",
                                       target_grade="A*")
    assert s.is_draft is True
    assert s.target_grade == "A*"

@pytest.mark.asyncio
async def test_upsert_idempotent(db_session, student):
    await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", exam_board="edexcel")
    s2 = await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", target_grade="B")
    assert s2.target_grade == "B"
    rows = await svc.list_subjects(db_session, student.id, include_drafts=True)
    assert len(rows) == 1

@pytest.mark.asyncio
async def test_finalize_flips_draft_and_sets_onboarded(db_session, student):
    await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", exam_board="edexcel", target_grade="A*")
    count = await svc.finalize_drafts(db_session, student.id)
    assert count == 1
    rows = await svc.list_subjects(db_session, student.id)
    assert all(not r.is_draft for r in rows)
    await db_session.refresh(student)
    assert student.onboarded_at is not None
    assert student.onboarding_complete is True

def test_is_supported_combo():
    assert svc.is_supported_combo("pure_mathematics", "edexcel", "a_level")
    assert svc.is_supported_combo("pure_mathematics", "cambridge", "a_level")
    assert not svc.is_supported_combo("physics", "edexcel", "a_level")
    assert not svc.is_supported_combo("pure_mathematics", "aqa", "a_level")
```

- [ ] **Step 2: Run tests — expect import failure**

Run: `pytest tests/test_learner_profile_service.py -v`

- [ ] **Step 3: Implement service**

```python
# app/services/learner_profile_service.py
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearnerSubject, Student
from app.core.syllabus_seed import SYLLABUS_VERSION

SUPPORTED_COMBOS: set[tuple[str, str, str]] = {
    ("pure_mathematics", "edexcel", "a_level"),
    ("pure_mathematics", "cambridge", "a_level"),
}


def is_supported_combo(subject: str, board: str, level: str = "a_level") -> bool:
    return (subject, board, level) in SUPPORTED_COMBOS


async def get_or_create_draft(db: AsyncSession, student_id: UUID) -> list[LearnerSubject]:
    res = await db.execute(select(LearnerSubject).where(LearnerSubject.student_id == student_id))
    return list(res.scalars().all())


async def upsert_subject_draft(db: AsyncSession, student_id: UUID, subject: str, **fields) -> LearnerSubject:
    res = await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = LearnerSubject(
            student_id=student_id,
            subject=subject,
            exam_board=fields.get("exam_board", "edexcel"),
            exam_level=fields.get("exam_level", "a_level"),
            target_grade=fields.get("target_grade", "A"),
            syllabus_version=SYLLABUS_VERSION,
            is_draft=True,
        )
        db.add(row)
    for k, v in fields.items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.flush()
    return row


async def list_subjects(db: AsyncSession, student_id: UUID, include_drafts: bool = False) -> list[LearnerSubject]:
    stmt = select(LearnerSubject).where(LearnerSubject.student_id == student_id)
    if not include_drafts:
        stmt = stmt.where(LearnerSubject.is_draft == False)  # noqa: E712
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def finalize_drafts(db: AsyncSession, student_id: UUID) -> int:
    rows = await get_or_create_draft(db, student_id)
    count = 0
    for r in rows:
        if r.is_draft:
            r.is_draft = False
            count += 1
    if count > 0:
        student = await db.get(Student, student_id)
        if student:
            student.onboarded_at = datetime.now(timezone.utc)
            student.onboarding_complete = True
    await db.flush()
    return count


async def update_subject(db: AsyncSession, student_id: UUID, subject_id: UUID, **fields) -> LearnerSubject:
    row = await db.get(LearnerSubject, subject_id)
    if row is None or row.student_id != student_id:
        raise ValueError("Subject not found")
    for k, v in fields.items():
        if hasattr(row, k) and k not in ("id", "student_id", "is_draft"):
            setattr(row, k, v)
    await db.flush()
    return row


async def update_preferences(db: AsyncSession, student_id: UUID, prefs: dict) -> Student:
    student = await db.get(Student, student_id)
    if student is None:
        raise ValueError("Student not found")
    allowed = {"worked_examples", "visual", "step_by_step", "practice"}
    student.preferences = {k: bool(v) for k, v in prefs.items() if k in allowed}
    await db.flush()
    return student
```

- [ ] **Step 4: Run tests — expect pass**

Run: `pytest tests/test_learner_profile_service.py -v`

- [ ] **Step 5: Commit**

```bash
git add app/services/learner_profile_service.py tests/test_learner_profile_service.py
git commit -m "Add learner_profile_service with draft lifecycle and preferences"
```

---

### Task 5: `readiness_service`

**Files:**
- Create: `app/services/readiness_service.py`
- Create: `app/core/grade_prediction.py`
- Create: `tests/test_readiness_service.py`

**Interfaces produced:**
- `async def compute_readiness_pct(db, student_id, subject, version) -> float`
- `async def write_snapshot_if_first_today(db, student_id, subject) -> ReadinessSnapshot | None`
- `async def get_trend_vs_28d(db, student_id, subject) -> dict | None` — `{prev_pct, new_pct, delta} | None`
- `app.core.grade_prediction.predict_grade(readiness_pct: float) -> str` — bucketing

- [ ] **Step 1: Write tests**

```python
# tests/test_readiness_service.py
import pytest
from datetime import date, timedelta
from app.services import readiness_service as svc
from app.core.grade_prediction import predict_grade
from app.db.models import MasteryState, SyllabusTopic, ReadinessSnapshot

@pytest.mark.asyncio
async def test_compute_readiness_zero_when_no_mastery(db_session, student, syllabus_edexcel_seeded):
    pct = await svc.compute_readiness_pct(db_session, student.id, "pure_mathematics", "2026.1")
    assert pct == 0.0

@pytest.mark.asyncio
async def test_compute_readiness_counts_only_competent_topics(db_session, student, syllabus_edexcel_seeded):
    db_session.add_all([
        MasteryState(student_id=student.id, subject="pure_mathematics", topic="integration_basics", mastery_score=0.8),
        MasteryState(student_id=student.id, subject="pure_mathematics", topic="differentiation_basics", mastery_score=0.6),  # below 0.7
    ])
    await db_session.flush()
    pct = await svc.compute_readiness_pct(db_session, student.id, "pure_mathematics", "2026.1")
    # 1 competent topic of 22 = 4.5%
    assert pct == pytest.approx(100.0 / 22, abs=0.5)

@pytest.mark.asyncio
async def test_snapshot_idempotent_per_day(db_session, student):
    snap1 = await svc.write_snapshot_if_first_today(db_session, student.id, "pure_mathematics")
    snap2 = await svc.write_snapshot_if_first_today(db_session, student.id, "pure_mathematics")
    assert snap1 is not None
    assert snap2 is None  # already written today

def test_grade_prediction_buckets():
    assert predict_grade(95) == "A*"
    assert predict_grade(80) == "A"
    assert predict_grade(70) == "B"
    assert predict_grade(50) == "C"
    assert predict_grade(35) == "D"
    assert predict_grade(20) == "E"
    assert predict_grade(0) == "E"
```

- [ ] **Step 2: Run — expect import errors**

- [ ] **Step 3: Implement grade prediction**

```python
# app/core/grade_prediction.py
def predict_grade(readiness_pct: float) -> str:
    """Heuristic readiness % → grade bucket. NOT a real model."""
    if readiness_pct >= 90: return "A*"
    if readiness_pct >= 75: return "A"
    if readiness_pct >= 60: return "B"
    if readiness_pct >= 45: return "C"
    if readiness_pct >= 30: return "D"
    return "E"
```

- [ ] **Step 4: Implement readiness service**

```python
# app/services/readiness_service.py
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MasteryState, SyllabusTopic, ReadinessSnapshot

COMPETENT_THRESHOLD = 0.7


async def compute_readiness_pct(db: AsyncSession, student_id: UUID, subject: str, version: str) -> float:
    total_q = select(func.count(SyllabusTopic.id)).where(
        SyllabusTopic.subject == subject,
        SyllabusTopic.version == version,
    )
    total = (await db.execute(total_q)).scalar() or 0
    if total == 0:
        return 0.0

    topic_ids_q = select(SyllabusTopic.topic_id).where(
        SyllabusTopic.subject == subject,
        SyllabusTopic.version == version,
    )
    topic_ids = {r[0] for r in (await db.execute(topic_ids_q)).all()}

    mastery_q = select(MasteryState.topic, MasteryState.mastery_score).where(
        MasteryState.student_id == student_id,
        MasteryState.subject == subject,
    )
    competent = 0
    for topic, score in (await db.execute(mastery_q)).all():
        if topic in topic_ids and (score or 0) >= COMPETENT_THRESHOLD:
            competent += 1
    return round(100.0 * competent / total, 1)


async def write_snapshot_if_first_today(db: AsyncSession, student_id: UUID, subject: str) -> ReadinessSnapshot | None:
    today = date.today()
    existing = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date == today,
        )
    )
    if existing.scalar_one_or_none():
        return None
    # Use the student's pinned syllabus version
    from app.db.models import LearnerSubject
    ls = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = ls.scalar() or "2026.1"
    pct = await compute_readiness_pct(db, student_id, subject, version)
    snap = ReadinessSnapshot(
        student_id=student_id, subject=subject,
        snapshot_date=today, readiness_pct=pct,
    )
    db.add(snap)
    await db.flush()
    return snap


async def get_trend_vs_28d(db: AsyncSession, student_id: UUID, subject: str) -> dict | None:
    today = date.today()
    cutoff = today - timedelta(days=7)
    history_count = await db.execute(
        select(func.count(ReadinessSnapshot.id)).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date <= cutoff,
        )
    )
    if (history_count.scalar() or 0) < 1:
        return None  # gate: ≥7 days of history
    today_snap = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date == today,
        )
    )
    today_row = today_snap.scalar_one_or_none()
    if not today_row:
        return None
    past_cutoff = today - timedelta(days=28)
    past = await db.execute(
        select(ReadinessSnapshot).where(
            ReadinessSnapshot.student_id == student_id,
            ReadinessSnapshot.subject == subject,
            ReadinessSnapshot.snapshot_date <= past_cutoff,
        ).order_by(ReadinessSnapshot.snapshot_date.desc()).limit(1)
    )
    past_row = past.scalar_one_or_none()
    if not past_row:
        return None
    return {
        "prev_pct": past_row.readiness_pct,
        "new_pct": today_row.readiness_pct,
        "delta": round(today_row.readiness_pct - past_row.readiness_pct, 1),
    }
```

- [ ] **Step 5: Add `syllabus_edexcel_seeded` fixture to `tests/conftest.py`**

```python
@pytest.fixture
async def syllabus_edexcel_seeded(db_session):
    from app.db.models import SyllabusTopic
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS, SYLLABUS_VERSION
    for t in EDEXCEL_9MA0_TOPICS:
        db_session.add(SyllabusTopic(
            exam_board="edexcel", subject="pure_mathematics",
            version=SYLLABUS_VERSION, **t,
        ))
    await db_session.flush()
```

- [ ] **Step 6: Run tests, commit**

```bash
pytest tests/test_readiness_service.py -v
git add app/services/readiness_service.py app/core/grade_prediction.py \
        tests/test_readiness_service.py tests/conftest.py
git commit -m "Add readiness_service (calc, snapshot, trend) and grade prediction bucketing"
```

---

### Task 6: `notification_service`

**Files:**
- Create: `app/services/notification_service.py`
- Create: `tests/test_notification_service.py`

**Interfaces produced:**
- `async def emit(db, student_id, type: str, payload: dict | None = None) -> Notification`
- `async def list_recent(db, student_id, limit=20) -> list[Notification]`
- `async def mark_read(db, student_id, notification_ids: list[UUID]) -> int`
- `async def mark_all_read(db, student_id) -> int`
- `async def unread_count(db, student_id) -> int`

**Notification types in this sub-project:** `readiness_increased | diagnostic_complete | subscription_renewed | session_reminder`

- [ ] **Step 1: Write tests**

```python
# tests/test_notification_service.py
import pytest
from uuid import uuid4
from app.services import notification_service as svc

@pytest.mark.asyncio
async def test_emit_creates_notification(db_session, student):
    n = await svc.emit(db_session, student.id, "readiness_increased",
                       payload={"subject": "pure_mathematics", "delta": 4.0})
    assert n.type == "readiness_increased"
    assert n.payload["delta"] == 4.0
    assert n.read_at is None

@pytest.mark.asyncio
async def test_list_returns_unread_first_newest_first(db_session, student):
    a = await svc.emit(db_session, student.id, "diagnostic_complete")
    b = await svc.emit(db_session, student.id, "readiness_increased")
    rows = await svc.list_recent(db_session, student.id)
    assert rows[0].id == b.id  # newest first
    assert rows[1].id == a.id

@pytest.mark.asyncio
async def test_mark_read(db_session, student):
    n = await svc.emit(db_session, student.id, "session_reminder")
    count = await svc.mark_read(db_session, student.id, [n.id])
    assert count == 1
    await db_session.refresh(n)
    assert n.read_at is not None

@pytest.mark.asyncio
async def test_unread_count(db_session, student):
    await svc.emit(db_session, student.id, "session_reminder")
    await svc.emit(db_session, student.id, "diagnostic_complete")
    assert await svc.unread_count(db_session, student.id) == 2
    await svc.mark_all_read(db_session, student.id)
    assert await svc.unread_count(db_session, student.id) == 0
```

- [ ] **Step 2: Run — expect failure**

- [ ] **Step 3: Implement service**

```python
# app/services/notification_service.py
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Notification


async def emit(db: AsyncSession, student_id: UUID, type: str,
               payload: dict | None = None) -> Notification:
    n = Notification(student_id=student_id, type=type, payload=payload or {})
    db.add(n)
    await db.flush()
    return n


async def list_recent(db: AsyncSession, student_id: UUID, limit: int = 20) -> list[Notification]:
    res = await db.execute(
        select(Notification)
        .where(Notification.student_id == student_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list(res.scalars().all())


async def mark_read(db: AsyncSession, student_id: UUID, notification_ids: list[UUID]) -> int:
    now = datetime.now(timezone.utc)
    res = await db.execute(
        update(Notification)
        .where(Notification.student_id == student_id,
               Notification.id.in_(notification_ids),
               Notification.read_at.is_(None))
        .values(read_at=now)
    )
    await db.flush()
    return res.rowcount or 0


async def mark_all_read(db: AsyncSession, student_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    res = await db.execute(
        update(Notification)
        .where(Notification.student_id == student_id,
               Notification.read_at.is_(None))
        .values(read_at=now)
    )
    await db.flush()
    return res.rowcount or 0


async def unread_count(db: AsyncSession, student_id: UUID) -> int:
    res = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.student_id == student_id,
            Notification.read_at.is_(None),
        )
    )
    return res.scalar() or 0
```

- [ ] **Step 4: Run tests, commit**

```bash
pytest tests/test_notification_service.py -v
git add app/services/notification_service.py tests/test_notification_service.py
git commit -m "Add notification_service (emit, list, mark-read, unread-count)"
```

---

### Task 7: PostHog feature-flag server client

**Files:**
- Create: `app/core/feature_flags.py`
- Modify: `requirements.txt` (add `posthog` if not already present — check first)
- Create: `tests/test_feature_flags.py`

**Interfaces produced:**
- `async def is_enabled(student_id: str | UUID, flag: str, default: bool = True) -> bool`
- `FLAGS` registry constant: `("dashboard_v2", "onboarding_v2", "session_engine_v2", "notifications_v2", "account_v2")`

**Note:** PostHog is already installed (used for analytics). This wraps `posthog.feature_enabled` with a 60s in-process cache and a default fallback.

- [ ] **Step 1: Check existing posthog usage**

Run: `grep -rn "posthog" app/core/ requirements.txt | head`

If `posthog` is already in `requirements.txt`, skip the install step.

- [ ] **Step 2: Write tests**

```python
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
```

- [ ] **Step 3: Implement**

```python
# app/core/feature_flags.py
import asyncio
import logging
import time
from typing import Iterable

logger = logging.getLogger(__name__)

FLAGS: Iterable[str] = (
    "dashboard_v2",
    "onboarding_v2",
    "session_engine_v2",
    "notifications_v2",
    "account_v2",
)

_CACHE: dict[tuple[str, str], tuple[bool, float]] = {}
_CACHE_TTL_SEC = 60


def _posthog_check(student_id: str, flag: str) -> bool:
    """Synchronous PostHog call, isolated so tests can patch it."""
    import posthog
    return bool(posthog.feature_enabled(flag, str(student_id)))


async def is_enabled(student_id, flag: str, default: bool = True) -> bool:
    if flag not in FLAGS:
        return default
    key = (str(student_id), flag)
    now = time.time()
    cached = _CACHE.get(key)
    if cached and cached[1] > now:
        return cached[0]
    try:
        result = await asyncio.to_thread(_posthog_check, str(student_id), flag)
    except Exception as exc:
        logger.warning("PostHog feature_enabled failed for %s/%s: %s", student_id, flag, exc)
        return default
    _CACHE[key] = (result, now + _CACHE_TTL_SEC)
    return result
```

- [ ] **Step 4: Run tests, commit**

```bash
pytest tests/test_feature_flags.py -v
git add app/core/feature_flags.py tests/test_feature_flags.py
git commit -m "Add PostHog feature-flag server client with cache + safe fallback"
```

---

## Phase C — Segment Handlers (5 tasks)

### Task 8: Segment handler protocol + state additions

**Files:**
- Create: `app/agents/handlers/__init__.py`
- Create: `app/agents/handlers/base.py`
- Modify: `app/workflows/state.py`

**Interfaces produced:**
- `SessionState` extended with `session_version: int`, `segment_plan: list[Segment]`, `current_segment_idx: int`, `segment_progress: dict`
- `Segment` TypedDict: `idx, intent, handler, topic, why, target_minutes, status, config`
- `class SegmentHandler(Protocol)` with `async def step(state, db, redis, user_input) -> HandlerResult`
- `class HandlerResult(TypedDict)` with `tutor_message, structured_cards, segment_complete, mastery_updates`
- `HANDLER_REGISTRY: dict[str, type[SegmentHandler]]`

- [ ] **Step 1: Extend SessionState**

In `app/workflows/state.py`, add to `SessionState`:

```python
from typing import TypedDict, Literal, Any

class Segment(TypedDict):
    idx: int
    intent: Literal["diagnose", "teach", "reinforce", "assess", "revise", "consolidate"]
    handler: Literal["diagnostic_question", "practice", "review", "mistakes"]
    topic: str | None
    why: str
    target_minutes: int
    status: Literal["pending", "in_progress", "done", "error"]
    config: dict[str, Any]

# Inside SessionState (add these fields):
    session_type: Literal["practice", "diagnostic"]
    session_version: int  # 1 = legacy single-phase, 2 = segment-based
    segment_plan: list[Segment]
    current_segment_idx: int
    segment_progress: dict[str, Any]  # per-handler scratch state
    preferences: dict[str, bool]      # injected from Student.preferences at session start
```

Update `initial_state(...)` to accept and default these fields.

- [ ] **Step 2: Define handler protocol**

`app/agents/handlers/__init__.py`:
```python
from app.agents.handlers.base import (
    SegmentHandler, HandlerResult, HANDLER_REGISTRY, register_handler,
)
__all__ = ["SegmentHandler", "HandlerResult", "HANDLER_REGISTRY", "register_handler"]
```

`app/agents/handlers/base.py`:
```python
from typing import Any, Protocol, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from app.workflows.state import SessionState


class HandlerResult(TypedDict, total=False):
    tutor_message: str | None         # streamed text to send
    structured_cards: list[dict]       # question/eval cards
    segment_complete: bool             # if True, orchestrator advances
    mastery_updates: list[dict]        # [{topic, delta, attempt_count}]
    error: str | None


class SegmentHandler(Protocol):
    name: str

    async def step(
        self,
        state: SessionState,
        db: AsyncSession,
        redis,
        user_input: str,
    ) -> HandlerResult: ...

    async def initial_message(self, state: SessionState) -> str | None:
        """Optional opener for the segment (e.g., 'Let's start with integration.')."""
        return None


HANDLER_REGISTRY: dict[str, SegmentHandler] = {}


def register_handler(handler: SegmentHandler) -> None:
    HANDLER_REGISTRY[handler.name] = handler
```

- [ ] **Step 3: Smoke test the protocol**

`tests/test_handler_protocol.py`:
```python
from app.agents.handlers import SegmentHandler, HANDLER_REGISTRY, register_handler

def test_registry_is_dict():
    assert isinstance(HANDLER_REGISTRY, dict)

def test_register_adds_handler():
    class Fake:
        name = "fake"
        async def step(self, state, db, redis, user_input): return {}
        async def initial_message(self, state): return None
    register_handler(Fake())
    assert "fake" in HANDLER_REGISTRY
    del HANDLER_REGISTRY["fake"]
```

- [ ] **Step 4: Run, commit**

```bash
pytest tests/test_handler_protocol.py -v
git add app/agents/handlers/ app/workflows/state.py tests/test_handler_protocol.py
git commit -m "Add segment handler protocol and extend SessionState for segment plans"
```

---

### Task 9: `diagnostic_question` handler

**Files:**
- Create: `app/agents/handlers/diagnostic.py`
- Create: `tests/test_diagnostic_handler.py`

**Interfaces consumed:** `SegmentHandler` protocol from Task 8; existing `generate_question` and `evaluate_answer` tools in `app/agents/tools.py`.

**Behavior:** one question per segment, no hints, no retries. After student answers, evaluate, write a `MasteryState` row with `mastery_score = 0.6 if correct else 0.2`, mark segment complete.

- [ ] **Step 1: Write tests**

```python
# tests/test_diagnostic_handler.py
import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.diagnostic import DiagnosticHandler

@pytest.mark.asyncio
async def test_first_step_emits_question_card(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "diagnose", "handler": "diagnostic_question",
        "topic": "integration_basics", "why": "...", "target_minutes": 1,
        "status": "in_progress", "config": {},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.diagnostic._generate_question", new=AsyncMock(return_value={"q":"…","mark_scheme":"…"})):
        result = await DiagnosticHandler().step(state, db_session, redis_client, user_input="")
    assert result["structured_cards"][0]["type"] == "question"
    assert result["segment_complete"] is False

@pytest.mark.asyncio
async def test_after_answer_evaluates_and_completes(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "diagnose", "handler": "diagnostic_question",
        "topic": "integration_basics", "why": "...", "target_minutes": 1,
        "status": "in_progress", "config": {"question_emitted": True, "question": "…", "mark_scheme": "…"},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.diagnostic._evaluate", new=AsyncMock(return_value={"correct": True, "marks_awarded": 1, "total_marks": 1, "feedback": "Good"})):
        result = await DiagnosticHandler().step(state, db_session, redis_client, user_input="x^2 + C")
    assert result["segment_complete"] is True
    assert result["mastery_updates"][0]["topic"] == "integration_basics"
    assert result["mastery_updates"][0]["mastery_score"] == 0.6
```

- [ ] **Step 2: Implement handler**

```python
# app/agents/handlers/diagnostic.py
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer


async def _generate_question(state: SessionState, topic: str) -> dict:
    # Thin wrapper so tests can patch.
    return await generate_question(
        subject=state["subject"], exam_board=state["exam_board"],
        topic=topic, difficulty="medium", with_hints=False,
    )


async def _evaluate(state: SessionState, question: str, mark_scheme: str, answer: str) -> dict:
    return await evaluate_answer(
        question=question, mark_scheme=mark_scheme, student_answer=answer,
    )


class DiagnosticHandler:
    name = "diagnostic_question"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})

        if not cfg.get("question_emitted"):
            q = await _generate_question(state, seg["topic"])
            cfg["question_emitted"] = True
            cfg["question"] = q["question"]
            cfg["mark_scheme"] = q["mark_scheme"]
            return {
                "tutor_message": "Here's your calibration question — no hints, no second tries. Take your time.",
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        # Student has answered
        eval_result = await _evaluate(state, cfg["question"], cfg["mark_scheme"], user_input)
        correct = bool(eval_result.get("correct"))
        return {
            "tutor_message": eval_result.get("feedback", ""),
            "structured_cards": [{"type": "evaluation", "data": eval_result}],
            "segment_complete": True,
            "mastery_updates": [{
                "topic": seg["topic"],
                "mastery_score": 0.6 if correct else 0.2,
                "attempt_delta": 1,
                "correct_delta": 1 if correct else 0,
            }],
        }

    async def initial_message(self, state: SessionState) -> str | None:
        return None  # opener emitted as part of first step


register_handler(DiagnosticHandler())
```

- [ ] **Step 3: Add `state_factory`, `redis_client` fixtures to `conftest.py`**

```python
@pytest.fixture
def state_factory(student):
    from app.workflows.state import initial_state
    def _make(**overrides):
        s = initial_state(student_id=str(student.id), subject="pure_mathematics")
        s.update(overrides)
        return s
    return _make

@pytest.fixture
async def redis_client():
    from app.core.redis_client import get_redis
    r = await get_redis()
    yield r
```

- [ ] **Step 4: Run tests, commit**

```bash
pytest tests/test_diagnostic_handler.py -v
git add app/agents/handlers/diagnostic.py tests/test_diagnostic_handler.py tests/conftest.py
git commit -m "Add diagnostic_question handler (single question, no hints, mid-band seed)"
```

---

### Task 10: `practice` handler (refactor of existing flow)

**Files:**
- Create: `app/agents/handlers/practice.py`
- Modify: `app/agents/tutor_agent.py` (extract reusable system-prompt builder + preference injection)
- Create: `tests/test_practice_handler.py`

**Interfaces consumed:** `SegmentHandler` protocol, existing tools.

**Behavior:** 1–3 questions per segment. Question → student attempt → evaluate (with hints allowed unless `allow_hints=false`). Terminating condition: max 3 questions OR `target_minutes` elapsed OR student answered correctly. `config` flags: `system_prompt_addendum`, `auto_answer`, `allow_hints`, `time_limit_seconds`.

- [ ] **Step 1: Extract reusable system-prompt builder**

In `app/agents/tutor_agent.py`, refactor `_build_system_prompt(state, signal)` so the preference block is appended via a new function:

```python
def _preferences_block(prefs: dict) -> str:
    if not prefs:
        return ""
    lines = ["<student_preferences>"]
    if prefs.get("worked_examples"):
        lines.append("- This student learns best from worked examples. When introducing a concept, show a complete worked example before asking them to attempt their own.")
    if prefs.get("step_by_step"):
        lines.append("- This student prefers granular step-by-step explanations. Break hints into the smallest meaningful steps.")
    if prefs.get("visual"):
        lines.append("- This student finds diagrams helpful. Where a diagram would clarify, describe one in ASCII or LaTeX even if not explicitly asked.")
    if prefs.get("practice"):
        lines.append("- This student learns by doing. Keep explanations short; prioritise getting them to a question quickly.")
    lines.append("</student_preferences>")
    return "\n".join(lines)
```

Append the result of `_preferences_block(state.get("preferences", {}))` to the existing prompt body.

- [ ] **Step 2: Write tests for practice handler**

```python
# tests/test_practice_handler.py
import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.practice import PracticeHandler

@pytest.mark.asyncio
async def test_first_step_emits_question(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": {},
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._generate_question", new=AsyncMock(return_value={"question":"…","mark_scheme":"…"})):
        r = await PracticeHandler().step(state, db_session, redis_client, "")
    assert r["structured_cards"][0]["type"] == "question"

@pytest.mark.asyncio
async def test_correct_answer_completes_segment(db_session, redis_client, state_factory):
    seg_cfg = {"questions_asked": 1, "current_question": {"question":"…","mark_scheme":"…"}}
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": seg_cfg,
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._evaluate", new=AsyncMock(return_value={"correct":True,"marks_awarded":3,"total_marks":3,"feedback":"Perfect."})):
        r = await PracticeHandler().step(state, db_session, redis_client, "x^2/2 + C")
    assert r["segment_complete"] is True

@pytest.mark.asyncio
async def test_max_questions_terminates(db_session, redis_client, state_factory):
    seg_cfg = {"questions_asked": 3, "current_question": {"question":"…","mark_scheme":"…"}}
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress", "config": seg_cfg,
    }], current_segment_idx=0)
    with patch("app.agents.handlers.practice._evaluate", new=AsyncMock(return_value={"correct":False,"marks_awarded":1,"total_marks":3,"feedback":"Close."})):
        r = await PracticeHandler().step(state, db_session, redis_client, "wrong")
    assert r["segment_complete"] is True  # hit MAX_QUESTIONS even though wrong
```

- [ ] **Step 3: Implement practice handler**

```python
# app/agents/handlers/practice.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer

MAX_QUESTIONS = 3


async def _generate_question(state: SessionState, topic: str, with_hints: bool) -> dict:
    return await generate_question(
        subject=state["subject"], exam_board=state["exam_board"],
        topic=topic, difficulty="medium", with_hints=with_hints,
    )


async def _evaluate(state, question: str, mark_scheme: str, answer: str) -> dict:
    return await evaluate_answer(question=question, mark_scheme=mark_scheme, student_answer=answer)


class PracticeHandler:
    name = "practice"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})
        allow_hints = cfg.get("allow_hints", True)

        # No current question → emit one
        if "current_question" not in cfg:
            q = await _generate_question(state, seg["topic"], with_hints=allow_hints)
            cfg["current_question"] = q
            cfg["questions_asked"] = cfg.get("questions_asked", 0) + 1
            return {
                "tutor_message": None,
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        # Student answered → evaluate
        cur = cfg["current_question"]
        eval_result = await _evaluate(state, cur["question"], cur["mark_scheme"], user_input)
        correct = bool(eval_result.get("correct"))

        # Mastery update for every attempt
        updates = [{
            "topic": seg["topic"],
            "mastery_score_delta": 0.1 if correct else -0.05,
            "attempt_delta": 1,
            "correct_delta": 1 if correct else 0,
        }]

        # Termination: correct OR max questions hit
        if correct or cfg["questions_asked"] >= MAX_QUESTIONS:
            return {
                "tutor_message": eval_result.get("feedback", ""),
                "structured_cards": [{"type": "evaluation", "data": eval_result}],
                "segment_complete": True,
                "mastery_updates": updates,
            }

        # Wrong but more questions allowed → emit next
        del cfg["current_question"]
        return {
            "tutor_message": eval_result.get("feedback", "") + " Let's try another.",
            "structured_cards": [{"type": "evaluation", "data": eval_result}],
            "segment_complete": False,
            "mastery_updates": updates,
        }

    async def initial_message(self, state):
        seg = state["segment_plan"][state["current_segment_idx"]]
        return f"Let's practise **{seg['topic'].replace('_', ' ')}**."


register_handler(PracticeHandler())
```

- [ ] **Step 4: Run tests, commit**

```bash
pytest tests/test_practice_handler.py -v
git add app/agents/handlers/practice.py app/agents/tutor_agent.py tests/test_practice_handler.py
git commit -m "Add practice handler with preference injection and configurable hints"
```

---

### Task 11: `review` and `mistakes` handlers

**Files:**
- Create: `app/agents/handlers/review.py`
- Create: `app/agents/handlers/mistakes.py`
- Create: `tests/test_review_handler.py`
- Create: `tests/test_mistakes_handler.py`

**`review` behavior:** re-asks a recent low-scoring question in slightly different framing. Always exactly one question per segment. Pulls the most recent below-threshold evaluation for the segment's topic from `today_focus_history` reasoning context or from session messages.

**`mistakes` behavior:** collects 1–3 below-threshold evaluations from the last N=3 sessions, walks the student through corrections one by one. Terminates when all collected mistakes have been addressed.

- [ ] **Step 1: Write tests for review handler**

```python
# tests/test_review_handler.py
import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.review import ReviewHandler

@pytest.mark.asyncio
async def test_review_pulls_recent_miss_and_emits_reframed(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "revise", "handler": "review",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress",
        "config": {"source": {"question": "Integrate x^2", "mark_scheme": "x^3/3 + C", "student_answer": "x^3"}}
    }], current_segment_idx=0)
    with patch("app.agents.handlers.review._reframe_question", new=AsyncMock(return_value={"question": "Integrate 2x", "mark_scheme": "x^2 + C"})):
        r = await ReviewHandler().step(state, db_session, redis_client, "")
    assert r["structured_cards"][0]["type"] == "question"
    assert "Integrate 2x" in r["structured_cards"][0]["data"]["question"]

@pytest.mark.asyncio
async def test_review_evaluates_and_completes(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "revise", "handler": "review",
        "topic": "integration_basics", "why": "...", "target_minutes": 10,
        "status": "in_progress",
        "config": {"current_question": {"question": "Integrate 2x", "mark_scheme": "x^2 + C"}}
    }], current_segment_idx=0)
    with patch("app.agents.handlers.review._evaluate", new=AsyncMock(return_value={"correct": True, "marks_awarded": 2, "total_marks": 2})):
        r = await ReviewHandler().step(state, db_session, redis_client, "x^2 + C")
    assert r["segment_complete"] is True
```

- [ ] **Step 2: Implement review handler**

```python
# app/agents/handlers/review.py
from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from app.agents.tools import generate_question, evaluate_answer
from sqlalchemy.ext.asyncio import AsyncSession


async def _reframe_question(state: SessionState, topic: str, source: dict) -> dict:
    # Ask LLM for a variant of the original question testing the same concept
    return await generate_question(
        subject=state["subject"], exam_board=state["exam_board"],
        topic=topic, difficulty="medium",
        reframe_of={"question": source["question"], "mark_scheme": source["mark_scheme"]},
    )


async def _evaluate(state, question, mark_scheme, answer):
    return await evaluate_answer(question=question, mark_scheme=mark_scheme, student_answer=answer)


class ReviewHandler:
    name = "review"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})

        if "current_question" not in cfg:
            source = cfg.get("source")
            if not source:
                # Fall back to fresh question if no source provided
                q = await generate_question(subject=state["subject"], exam_board=state["exam_board"],
                                            topic=seg["topic"], difficulty="medium")
            else:
                q = await _reframe_question(state, seg["topic"], source)
            cfg["current_question"] = q
            return {
                "tutor_message": "Let's revisit this — same concept, slightly different framing.",
                "structured_cards": [{"type": "question", "data": q}],
                "segment_complete": False,
            }

        cur = cfg["current_question"]
        result = await _evaluate(state, cur["question"], cur["mark_scheme"], user_input)
        correct = bool(result.get("correct"))
        return {
            "tutor_message": result.get("feedback", ""),
            "structured_cards": [{"type": "evaluation", "data": result}],
            "segment_complete": True,
            "mastery_updates": [{
                "topic": seg["topic"],
                "mastery_score_delta": 0.15 if correct else 0.0,
                "attempt_delta": 1,
                "correct_delta": 1 if correct else 0,
            }],
        }


register_handler(ReviewHandler())
```

- [ ] **Step 3: Write tests for mistakes handler**

```python
# tests/test_mistakes_handler.py
import pytest
from unittest.mock import patch, AsyncMock
from app.agents.handlers.mistakes import MistakesHandler

@pytest.mark.asyncio
async def test_mistakes_walks_each_collected_item(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "consolidate", "handler": "mistakes",
        "topic": None, "why": "...", "target_minutes": 5,
        "status": "in_progress",
        "config": {"mistakes": [
            {"question": "Q1", "mark_scheme": "MS1", "student_answer": "wrong1"},
            {"question": "Q2", "mark_scheme": "MS2", "student_answer": "wrong2"},
        ]}
    }], current_segment_idx=0)
    # Step 1: emit first correction
    r = await MistakesHandler().step(state, db_session, redis_client, "")
    assert r["segment_complete"] is False
    assert "Q1" in r["tutor_message"]

@pytest.mark.asyncio
async def test_mistakes_completes_when_list_exhausted(db_session, redis_client, state_factory):
    state = state_factory(segment_plan=[{
        "idx": 0, "intent": "consolidate", "handler": "mistakes",
        "topic": None, "why": "...", "target_minutes": 5,
        "status": "in_progress",
        "config": {"mistakes": [], "idx": 0}
    }], current_segment_idx=0)
    r = await MistakesHandler().step(state, db_session, redis_client, "ok")
    assert r["segment_complete"] is True
```

- [ ] **Step 4: Implement mistakes handler**

```python
# app/agents/handlers/mistakes.py
from app.agents.handlers.base import HandlerResult, register_handler
from app.workflows.state import SessionState
from sqlalchemy.ext.asyncio import AsyncSession


class MistakesHandler:
    name = "mistakes"

    async def step(self, state: SessionState, db: AsyncSession, redis, user_input: str) -> HandlerResult:
        seg = state["segment_plan"][state["current_segment_idx"]]
        cfg = seg.setdefault("config", {})
        mistakes = cfg.get("mistakes", [])
        idx = cfg.get("idx", 0)

        if idx >= len(mistakes):
            return {
                "tutor_message": "Nice work — that's all the recent mistakes locked in.",
                "structured_cards": [],
                "segment_complete": True,
            }

        m = mistakes[idx]
        cfg["idx"] = idx + 1
        # Walk the student through the correct approach in narrative form
        msg = (
            f"Earlier you answered:\n\n> {m['student_answer']}\n\n"
            f"The mark scheme expected:\n\n> {m['mark_scheme']}\n\n"
            f"Let's walk through why."
        )
        return {
            "tutor_message": msg,
            "structured_cards": [{"type": "mistake_review", "data": m}],
            "segment_complete": False,
        }


register_handler(MistakesHandler())
```

- [ ] **Step 5: Run all handler tests, commit**

```bash
pytest tests/test_review_handler.py tests/test_mistakes_handler.py -v
git add app/agents/handlers/review.py app/agents/handlers/mistakes.py \
        tests/test_review_handler.py tests/test_mistakes_handler.py
git commit -m "Add review and mistakes segment handlers"
```

---

### Task 12: Orchestrator + session versioning shim

**Files:**
- Create: `app/agents/orchestrator.py`
- Modify: `app/services/session_service.py` (route through orchestrator; remove phase-advance logic)
- Create: `tests/test_orchestrator.py`

**Interfaces produced:**
- `async def step_session(state, db, redis, user_input) -> dict` — returns `{tutor_message, structured_cards, state_changes, session_complete}`
- `def shim_v1_to_v2(state) -> SessionState` — transparent legacy migration
- `async def advance_segment(state, db) -> SessionState`

- [ ] **Step 1: Tests**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import patch, AsyncMock
from app.agents import orchestrator
from app.agents.handlers import register_handler, HANDLER_REGISTRY

class _Fake:
    name = "_fake"
    async def step(self, state, db, redis, user_input):
        return {"tutor_message": "ok", "structured_cards": [], "segment_complete": True}
    async def initial_message(self, state): return None

@pytest.fixture(autouse=True)
def _register_fake():
    register_handler(_Fake())
    yield
    HANDLER_REGISTRY.pop("_fake", None)

@pytest.mark.asyncio
async def test_step_invokes_current_handler(db_session, redis_client, state_factory):
    state = state_factory(
        session_version=2,
        segment_plan=[
            {"idx":0,"intent":"diagnose","handler":"_fake","topic":"t","why":"","target_minutes":1,"status":"in_progress","config":{}},
            {"idx":1,"intent":"reinforce","handler":"_fake","topic":"t","why":"","target_minutes":1,"status":"pending","config":{}},
        ],
        current_segment_idx=0,
    )
    r = await orchestrator.step_session(state, db_session, redis_client, "")
    assert r["state_changes"]["current_segment_idx"] == 1

@pytest.mark.asyncio
async def test_last_segment_marks_session_complete(db_session, redis_client, state_factory):
    state = state_factory(
        session_version=2,
        segment_plan=[
            {"idx":0,"intent":"diagnose","handler":"_fake","topic":"t","why":"","target_minutes":1,"status":"in_progress","config":{}},
        ],
        current_segment_idx=0,
    )
    r = await orchestrator.step_session(state, db_session, redis_client, "")
    assert r["session_complete"] is True

def test_shim_v1_to_v2_wraps_in_single_segment(state_factory):
    s = state_factory(session_version=1, segment_plan=[], current_segment_idx=0)
    s["subject"] = "pure_mathematics"
    s["session_phase"] = "main"
    out = orchestrator.shim_v1_to_v2(s)
    assert out["session_version"] == 2
    assert len(out["segment_plan"]) == 1
    assert out["segment_plan"][0]["handler"] == "practice"
```

- [ ] **Step 2: Implement orchestrator**

```python
# app/agents/orchestrator.py
from app.agents.handlers import HANDLER_REGISTRY
from app.workflows.state import SessionState


def shim_v1_to_v2(state: SessionState) -> SessionState:
    """Wrap a legacy v1 session in a single-segment v2 plan at load time."""
    if state.get("session_version") == 2:
        return state
    state["session_version"] = 2
    state["session_type"] = state.get("session_type", "practice")
    if not state.get("segment_plan"):
        state["segment_plan"] = [{
            "idx": 0,
            "intent": "reinforce",
            "handler": "practice",
            "topic": None,
            "why": "",
            "target_minutes": 15,
            "status": "in_progress",
            "config": {},
        }]
    state.setdefault("current_segment_idx", 0)
    state.setdefault("segment_progress", {})
    return state


async def step_session(state: SessionState, db, redis, user_input: str) -> dict:
    state = shim_v1_to_v2(state)
    plan = state["segment_plan"]
    idx = state["current_segment_idx"]
    seg = plan[idx]
    handler = HANDLER_REGISTRY.get(seg["handler"])
    if handler is None:
        return {
            "tutor_message": "We hit a snag — please retry.",
            "structured_cards": [],
            "state_changes": {},
            "session_complete": False,
            "error": f"unknown handler {seg['handler']}",
        }

    result = await handler.step(state, db, redis, user_input)
    state_changes = {}
    state_changes["segment_plan"] = plan  # mutated in-place by handler via config

    if result.get("segment_complete"):
        seg["status"] = "done"
        next_idx = idx + 1
        if next_idx < len(plan):
            plan[next_idx]["status"] = "in_progress"
            state_changes["current_segment_idx"] = next_idx
            next_handler = HANDLER_REGISTRY.get(plan[next_idx]["handler"])
            opener = await next_handler.initial_message(state) if next_handler else None
            transition = f"Nice work — let's move on to your {plan[next_idx]['intent']} segment."
            result["tutor_message"] = (
                (result.get("tutor_message") or "") + "\n\n" + transition +
                (("\n\n" + opener) if opener else "")
            ).strip()
            session_complete = False
        else:
            state_changes["session_complete"] = True
            session_complete = True
    else:
        session_complete = False

    return {
        "tutor_message": result.get("tutor_message"),
        "structured_cards": result.get("structured_cards", []),
        "mastery_updates": result.get("mastery_updates", []),
        "state_changes": state_changes,
        "session_complete": session_complete,
    }
```

- [ ] **Step 3: Refactor `session_service.stream_response` to route through orchestrator**

In `app/services/session_service.py`, replace the body of `stream_response` so it:
1. Loads session state from Redis (or rebuilds from Postgres)
2. Calls `await orchestrator.step_session(state, db, redis, user_input)`
3. Applies `state_changes` and `mastery_updates` to DB
4. Streams `tutor_message` and emits `structured_cards`
5. If `session_complete`, sets `TutorSession.ended_at = now()` and invalidates the Today's Focus Redis cache for the student/subject/today

Keep the existing 3-model Groq fallback intact for any LLM calls inside handlers.

- [ ] **Step 4: Run tests, commit**

```bash
pytest tests/test_orchestrator.py -v
git add app/agents/orchestrator.py app/services/session_service.py tests/test_orchestrator.py
git commit -m "Add orchestrator (segment transitions, v1→v2 shim) and route session_service through it"
```

---

## Phase D — Today's Focus + Dashboard Backend (3 tasks)

### Task 13: `today_focus_service` shape selector + slot fillers

**Files:**
- Create: `app/services/today_focus_service.py`
- Create: `tests/test_today_focus_service.py`

**Interfaces produced:**
- `def select_shape(student_state: dict) -> str` — `"onboarding" | "build" | "default" | "exam_ready"`
- `async def build_segment_plan(db, student_id, subject, shape) -> tuple[list[Segment], list[dict]]` — returns `(plan, reasoning)`
- `WHY_TEMPLATES: dict[str, str]`
- `GENERATOR_VERSION = "1.0"`

- [ ] **Step 1: Tests**

```python
# tests/test_today_focus_service.py
import pytest
from app.services import today_focus_service as svc

def test_select_shape_onboarding_when_few_sessions():
    assert svc.select_shape({"sessions_count": 0, "readiness_pct": 0, "days_until_exam": 100, "avg_mastery_trend_7d": 0}) == "onboarding"
    assert svc.select_shape({"sessions_count": 2, "readiness_pct": 30, "days_until_exam": 100, "avg_mastery_trend_7d": 0}) == "onboarding"

def test_select_shape_exam_ready_when_close_and_high_readiness():
    assert svc.select_shape({"sessions_count": 50, "readiness_pct": 80, "days_until_exam": 10, "avg_mastery_trend_7d": 0.05}) == "exam_ready"

def test_select_shape_build_when_struggling():
    assert svc.select_shape({"sessions_count": 20, "readiness_pct": 30, "days_until_exam": 100, "avg_mastery_trend_7d": -0.1}) == "build"

def test_select_shape_default_otherwise():
    assert svc.select_shape({"sessions_count": 20, "readiness_pct": 55, "days_until_exam": 60, "avg_mastery_trend_7d": 0.02}) == "default"

@pytest.mark.asyncio
async def test_build_plan_default_shape_three_segments(db_session, student, syllabus_edexcel_seeded):
    plan, reasoning = await svc.build_segment_plan(db_session, student.id, "pure_mathematics", "default")
    assert len(plan) == 3
    intents = [s["intent"] for s in plan]
    assert intents == ["revise", "reinforce", "consolidate"]
    for seg in plan:
        assert seg["why"]  # all segments have a why string
```

- [ ] **Step 2: Implement service**

```python
# app/services/today_focus_service.py
from datetime import date
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    LearnerSubject, MasteryState, SyllabusTopic, TutorSession,
    TodayFocusHistory,
)

GENERATOR_VERSION = "1.0"

WHY_TEMPLATES = {
    "diagnose": "Let's see where you are with {topic}.",
    "teach": "This topic is new for you — let's build it up.",
    "reinforce": "Your mastery on {topic} dropped to {pct}%. Let's bring it back up.",
    "assess": "Time to test what you've learned — no hints this round.",
    "revise": "Quick revisit of {topic} — let's lock it in.",
    "consolidate": "Reviewing concepts you've nearly mastered to make them stick.",
}


def select_shape(student_state: dict) -> str:
    if student_state["sessions_count"] < 3:
        return "onboarding"
    if student_state["days_until_exam"] <= 14 and student_state["readiness_pct"] >= 75:
        return "exam_ready"
    if student_state["readiness_pct"] < 40 or student_state["avg_mastery_trend_7d"] < -0.05:
        return "build"
    return "default"


def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()


async def _pick_topics_by_mastery(db, student_id: UUID, subject: str) -> list[tuple[str, float, int]]:
    """Return [(topic, mastery_score, attempts)] sorted by mastery ascending."""
    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score, MasteryState.total_attempts)
        .where(MasteryState.student_id == student_id, MasteryState.subject == subject)
        .order_by(MasteryState.mastery_score.asc())
    )
    return list(res.all())


async def _pick_next_syllabus_topic(db, subject: str, version: str, exclude: set[str]) -> str | None:
    res = await db.execute(
        select(SyllabusTopic.topic_id)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.version == version)
        .order_by(SyllabusTopic.ordinal.asc())
    )
    for (tid,) in res.all():
        if tid not in exclude:
            return tid
    return None


async def build_segment_plan(db: AsyncSession, student_id: UUID, subject: str, shape: str) -> tuple[list, list]:
    ls = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id, LearnerSubject.subject == subject,
        )
    )
    version = ls.scalar() or "2026.1"
    mastery = await _pick_topics_by_mastery(db, student_id, subject)
    studied = {t for t, _, _ in mastery}
    weakest = mastery[0] if mastery else None

    plan: list = []
    reasoning: list = []

    if shape == "default":
        # 1. revise weakest with prior attempts
        t1 = weakest[0] if weakest else await _pick_next_syllabus_topic(db, subject, version, studied)
        plan.append(_segment(0, "revise", "review", t1, _format_topic(t1) if t1 else "your weakest area", 10))
        # 2. reinforce 2nd-weakest
        t2 = mastery[1][0] if len(mastery) > 1 else await _pick_next_syllabus_topic(db, subject, version, studied | {t1})
        pct = int((mastery[1][1] if len(mastery) > 1 else 0) * 100)
        plan.append(_segment(1, "reinforce", "practice", t2,
                             WHY_TEMPLATES["reinforce"].format(topic=_format_topic(t2), pct=pct), 15))
        # 3. consolidate / mistakes
        plan.append(_segment(2, "consolidate", "mistakes", None,
                             WHY_TEMPLATES["consolidate"], 5))
    elif shape == "onboarding":
        t1 = await _pick_next_syllabus_topic(db, subject, version, studied)
        plan.append(_segment(0, "teach", "practice", t1, "Let's start with the first topic.", 10,
                             config={"system_prompt_addendum": "Open with a worked example before asking the student to attempt.", "allow_hints": True}))
        plan.append(_segment(1, "teach", "practice", t1, "I'll walk through a worked example.", 10,
                             config={"auto_answer": True}))
        plan.append(_segment(2, "assess", "practice", t1, WHY_TEMPLATES["assess"], 5,
                             config={"allow_hints": False}))
    elif shape == "build":
        t1 = await _pick_next_syllabus_topic(db, subject, version, studied) or (weakest[0] if weakest else None)
        plan.append(_segment(0, "teach", "practice", t1, "Let's build this up properly.", 15,
                             config={"system_prompt_addendum": "Open with a worked example before asking the student to attempt."}))
        plan.append(_segment(1, "reinforce", "practice", weakest[0] if weakest else t1,
                             WHY_TEMPLATES["reinforce"].format(topic=_format_topic(weakest[0] if weakest else t1),
                                                                pct=int((weakest[1] if weakest else 0) * 100)), 10))
        plan.append(_segment(2, "revise", "review", weakest[0] if weakest else t1, WHY_TEMPLATES["revise"].format(topic=_format_topic(weakest[0] if weakest else t1)), 5))
    else:  # exam_ready
        t = weakest[0] if weakest else None
        plan.append(_segment(0, "assess", "practice", t, WHY_TEMPLATES["assess"], 20,
                             config={"time_limit_seconds": 1200}))
        plan.append(_segment(1, "consolidate", "mistakes", None, WHY_TEMPLATES["consolidate"], 10))
        plan.append(_segment(2, "revise", "mistakes", None, "Quick flash review of recent misses.", 5,
                             config={"pace": "rapid"}))

    for seg in plan:
        reasoning.append({"segment_idx": seg["idx"], "factors": {"shape": shape, "topic": seg.get("topic")}})
    return plan, reasoning


def _segment(idx, intent, handler, topic, why, target_minutes, config=None):
    return {
        "idx": idx, "intent": intent, "handler": handler,
        "topic": topic, "why": why, "target_minutes": target_minutes,
        "status": "pending" if idx > 0 else "in_progress",
        "config": config or {},
    }
```

- [ ] **Step 3: Run tests, commit**

```bash
pytest tests/test_today_focus_service.py -v
git add app/services/today_focus_service.py tests/test_today_focus_service.py
git commit -m "Add today_focus_service shape selector and slot fillers"
```

---

### Task 14: Today's Focus caching + persistence

**Files:**
- Modify: `app/services/today_focus_service.py`
- Create: `tests/test_today_focus_cache.py`

**Interfaces produced (added to existing service):**
- `async def get_or_generate(db, redis, student_id, subject) -> dict` — main entry point; reads Redis cache, persists to history, returns `{shape, segment_plan, reasoning, generator_version, generated_at, expires_at}`
- `async def invalidate_today(redis, student_id, subject) -> None`
- `def _cache_key(student_id, subject, focus_date) -> str`

- [ ] **Step 1: Tests**

```python
# tests/test_today_focus_cache.py
import json
import pytest
from app.services import today_focus_service as svc

@pytest.mark.asyncio
async def test_first_call_generates_and_caches(db_session, redis_client, student, syllabus_edexcel_seeded):
    out = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    assert out["generator_version"] == svc.GENERATOR_VERSION
    cached = await redis_client.get(svc._cache_key(student.id, "pure_mathematics", out["focus_date"]))
    assert cached is not None

@pytest.mark.asyncio
async def test_second_call_reads_cache(db_session, redis_client, student, syllabus_edexcel_seeded):
    a = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    b = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    assert a["segment_plan"] == b["segment_plan"]  # exact same plan

@pytest.mark.asyncio
async def test_invalidate_clears_cache(db_session, redis_client, student, syllabus_edexcel_seeded):
    await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    await svc.invalidate_today(redis_client, student.id, "pure_mathematics")
    # Next call regenerates (different generated_at)
    out2 = await svc.get_or_generate(db_session, redis_client, student.id, "pure_mathematics")
    assert out2 is not None
```

- [ ] **Step 2: Implement cache layer**

Append to `app/services/today_focus_service.py`:

```python
import json
from datetime import date, datetime, timedelta, timezone
from app.db.models import TodayFocusHistory


def _cache_key(student_id, subject: str, focus_date: date) -> str:
    return f"today_focus:{student_id}:{subject}:{focus_date.isoformat()}"


async def _get_session_count(db, student_id, subject) -> int:
    res = await db.execute(
        select(func.count(TutorSession.id)).where(
            TutorSession.student_id == student_id,
            TutorSession.subject == subject,
        )
    )
    return res.scalar() or 0


async def _days_until_exam(db, student_id, subject) -> int:
    res = await db.execute(
        select(LearnerSubject.exam_date).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    exam_date = res.scalar()
    if not exam_date:
        return 180
    return max(0, (exam_date - date.today()).days)


async def _student_state(db, student_id, subject) -> dict:
    from app.services.readiness_service import compute_readiness_pct
    return {
        "sessions_count": await _get_session_count(db, student_id, subject),
        "days_until_exam": await _days_until_exam(db, student_id, subject),
        "readiness_pct": await compute_readiness_pct(db, student_id, subject, "2026.1"),
        "avg_mastery_trend_7d": 0.0,  # TODO: compute from snapshots when available
    }


async def get_or_generate(db: AsyncSession, redis, student_id, subject: str) -> dict:
    today = date.today()
    key = _cache_key(student_id, subject, today)

    cached = await redis.get(key)
    if cached:
        return json.loads(cached if isinstance(cached, str) else cached.decode())

    # Idempotency lock — only one writer per day per (student, subject)
    lock_key = f"{key}:lock"
    got_lock = await redis.set(lock_key, "1", nx=True, ex=30)
    if not got_lock:
        # Another worker is generating; brief poll
        for _ in range(20):
            cached = await redis.get(key)
            if cached:
                return json.loads(cached if isinstance(cached, str) else cached.decode())
            import asyncio; await asyncio.sleep(0.1)

    state = await _student_state(db, student_id, subject)
    shape = select_shape(state)
    plan, reasoning = await build_segment_plan(db, student_id, subject, shape)
    expires = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    payload = {
        "shape": shape,
        "segment_plan": plan,
        "reasoning": reasoning,
        "generator_version": GENERATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires.isoformat(),
        "focus_date": today.isoformat(),
    }

    db.add(TodayFocusHistory(
        student_id=student_id, subject=subject, focus_date=today,
        generator_version=GENERATOR_VERSION, shape=shape,
        segment_plan=plan, reasoning=reasoning, expires_at=expires,
    ))
    await db.flush()

    ttl_sec = int((expires - datetime.now(timezone.utc)).total_seconds())
    await redis.set(key, json.dumps(payload), ex=ttl_sec)
    return payload


async def invalidate_today(redis, student_id, subject: str) -> None:
    await redis.delete(_cache_key(student_id, subject, date.today()))
```

- [ ] **Step 3: Run, commit**

```bash
pytest tests/test_today_focus_cache.py -v
git add app/services/today_focus_service.py tests/test_today_focus_cache.py
git commit -m "Add today_focus caching to Redis + persistence to today_focus_history"
```

---

### Task 15: Dashboard payload endpoint

**Files:**
- Create: `app/api/v1/endpoints/dashboard.py`
- Create: `app/schemas/dashboard.py`
- Modify: `app/main.py` (mount router)
- Create: `tests/test_dashboard_endpoint.py`

**Interfaces produced:**
- `GET /api/v1/dashboard/{subject}` → `DashboardPayload`
- `DashboardPayload`: `{subject, exam_date, days_until_exam, target_grade, predicted_grade, readiness_pct, readiness_trend, today_focus, resume_session, recent_activity, strong_topics, weak_topics, subject_options}`

- [ ] **Step 1: Tests**

```python
# tests/test_dashboard_endpoint.py
import pytest

@pytest.mark.asyncio
async def test_dashboard_returns_payload(authed_client, student_with_subject):
    res = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert res.status_code == 200
    body = res.json()
    assert "readiness_pct" in body
    assert "today_focus" in body
    assert body["target_grade"] == "A*"

@pytest.mark.asyncio
async def test_dashboard_404_for_unsupported_subject(authed_client):
    res = await authed_client.get("/api/v1/dashboard/physics")
    assert res.status_code == 404
```

- [ ] **Step 2: Schema**

```python
# app/schemas/dashboard.py
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel


class SegmentOut(BaseModel):
    idx: int
    intent: str
    handler: str
    topic: str | None
    why: str
    target_minutes: int
    status: str


class TodayFocusOut(BaseModel):
    shape: str
    segment_plan: list[SegmentOut]
    total_minutes: int
    generated_at: datetime


class ResumeSessionOut(BaseModel):
    session_id: str
    completed_segments: int
    total_segments: int


class TopicMastery(BaseModel):
    topic: str
    topic_name: str
    mastery_pct: int


class TrendOut(BaseModel):
    prev_pct: float
    new_pct: float
    delta: float


class RecentActivityOut(BaseModel):
    last_studied: date | None
    summary: str | None  # "Integration Practice · scored 78%"
    cold: bool          # true if >3 days since last study


class DashboardPayload(BaseModel):
    subject: str
    exam_date: date | None
    days_until_exam: int | None
    target_grade: str
    predicted_grade: str | None
    readiness_pct: float
    readiness_trend: TrendOut | None
    today_focus: TodayFocusOut
    resume_session: ResumeSessionOut | None
    recent_activity: RecentActivityOut | None
    strong_topics: list[TopicMastery]
    weak_topics: list[TopicMastery]
    subject_options: list[str]  # for switcher
```

- [ ] **Step 3: Endpoint**

```python
# app/api/v1/endpoints/dashboard.py
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student, LearnerSubject, MasteryState, TutorSession, SyllabusTopic
from app.core.redis_client import get_redis
from app.services import readiness_service, today_focus_service
from app.services.learner_profile_service import is_supported_combo
from app.core.grade_prediction import predict_grade
from app.schemas.dashboard import (
    DashboardPayload, SegmentOut, TodayFocusOut, ResumeSessionOut,
    TopicMastery, TrendOut, RecentActivityOut,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{subject}", response_model=DashboardPayload)
async def get_dashboard(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    ls_row = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.subject == subject,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not ls_row:
        raise HTTPException(404, "Subject not configured for this student")
    if not is_supported_combo(ls_row.subject, ls_row.exam_board, ls_row.exam_level):
        raise HTTPException(404, "Subject not yet supported")

    redis = await get_redis()
    # Snapshot today if not yet written
    await readiness_service.write_snapshot_if_first_today(db, student.id, subject)
    readiness_pct = await readiness_service.compute_readiness_pct(db, student.id, subject, ls_row.syllabus_version)
    trend = await readiness_service.get_trend_vs_28d(db, student.id, subject)

    today_focus = await today_focus_service.get_or_generate(db, redis, student.id, subject)

    # Resume session detection (active session within last 24h)
    cutoff = date.today() - timedelta(hours=24)
    rs_row = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
            TutorSession.ended_at.is_(None),
        ).order_by(TutorSession.started_at.desc())
    )).scalars().first()
    resume = None
    if rs_row and rs_row.started_at and rs_row.started_at.date() >= cutoff:
        plan = rs_row.segment_plan or []
        if rs_row.current_segment_idx < len(plan):
            resume = ResumeSessionOut(
                session_id=str(rs_row.id),
                completed_segments=rs_row.current_segment_idx,
                total_segments=len(plan),
            )
    elif rs_row:
        # Stale resume — auto-close
        from datetime import datetime, timezone, timedelta as td
        rs_row.ended_at = rs_row.started_at + td(hours=24)
        await db.flush()

    # Strong / weak topics
    mastery = (await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score).where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
        )
    )).all()
    topic_name_map = dict((await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name).where(
            SyllabusTopic.subject == subject, SyllabusTopic.version == ls_row.syllabus_version,
        )
    )).all())
    def _tm(t, s):
        return TopicMastery(topic=t, topic_name=topic_name_map.get(t, t), mastery_pct=int((s or 0) * 100))
    sorted_m = sorted(mastery, key=lambda r: r[1] or 0)
    weak = [_tm(t, s) for t, s in sorted_m[:3]]
    strong = [_tm(t, s) for t, s in sorted(mastery, key=lambda r: -(r[1] or 0))[:3]]

    # Recent activity
    last_session = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == student.id,
            TutorSession.subject == subject,
            TutorSession.ended_at.is_not(None),
        ).order_by(TutorSession.ended_at.desc()).limit(1)
    )).scalars().first()
    recent = None
    if last_session:
        days_ago = (date.today() - last_session.ended_at.date()).days
        recent = RecentActivityOut(
            last_studied=last_session.ended_at.date(),
            summary=f"{last_session.topic or 'Session'}",
            cold=days_ago >= 3,
        )

    # Subject switcher options
    all_subjects = (await db.execute(
        select(LearnerSubject.subject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalars().all()

    plan_out = [SegmentOut(**s) for s in today_focus["segment_plan"]]
    return DashboardPayload(
        subject=subject,
        exam_date=ls_row.exam_date,
        days_until_exam=(ls_row.exam_date - date.today()).days if ls_row.exam_date else None,
        target_grade=ls_row.target_grade,
        predicted_grade=predict_grade(readiness_pct) if trend else None,
        readiness_pct=readiness_pct,
        readiness_trend=TrendOut(**trend) if trend else None,
        today_focus=TodayFocusOut(
            shape=today_focus["shape"],
            segment_plan=plan_out,
            total_minutes=sum(s.target_minutes for s in plan_out),
            generated_at=today_focus["generated_at"],
        ),
        resume_session=resume,
        recent_activity=recent,
        strong_topics=strong,
        weak_topics=weak,
        subject_options=list(all_subjects),
    )
```

- [ ] **Step 4: Wire router in `app/main.py`**

```python
from app.api.v1.endpoints.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 5: Run, commit**

```bash
pytest tests/test_dashboard_endpoint.py -v
git add app/api/v1/endpoints/dashboard.py app/schemas/dashboard.py app/main.py tests/test_dashboard_endpoint.py
git commit -m "Add dashboard endpoint with payload assembly (readiness, today_focus, resume, recent, topics)"
```

---

## Phase E — Backend API Surfaces (4 tasks)

### Task 16: Onboarding endpoints

**Files:**
- Create: `app/api/v1/endpoints/onboarding.py`
- Create: `app/schemas/onboarding.py`
- Modify: `app/main.py`
- Create: `tests/test_onboarding_endpoints.py`

**Endpoints:**
- `GET /api/v1/onboarding/state` → `{next_step, draft}` — server-driven step routing
- `POST /api/v1/onboarding/education-system` `{system}` → `{ok}`
- `POST /api/v1/onboarding/subjects` `{subjects: [str]}` → `{ok}`
- `POST /api/v1/onboarding/exam-board` `{subject_boards: {subject: board}}`
- `POST /api/v1/onboarding/exam-date` `{subject_dates: {subject: iso_date | "unknown"}}`
- `POST /api/v1/onboarding/target-grade` `{subject_grades: {subject: {current?, target}}}`
- `POST /api/v1/onboarding/preferences` `{worked_examples, visual, step_by_step, practice}` → `{ok}`
- `POST /api/v1/onboarding/finalize` → `{ok, redirect_to: "/dashboard"}` — flips drafts, sets `onboarded_at`, computes `recommended_minutes_per_day`, emits `onboarding_completed` analytics event

**Step ordering (server-side):** if `education_system` missing → return `next_step="education-system"`; else if subjects missing → `subjects`; etc.

- [ ] **Step 1: Tests covering wizard flow**

```python
# tests/test_onboarding_endpoints.py
import pytest

@pytest.mark.asyncio
async def test_state_returns_first_step_for_new_user(authed_client):
    res = await authed_client.get("/api/v1/onboarding/state")
    assert res.status_code == 200
    assert res.json()["next_step"] == "welcome"

@pytest.mark.asyncio
async def test_education_system_post_advances(authed_client):
    r1 = await authed_client.post("/api/v1/onboarding/education-system", json={"system": "a_level"})
    assert r1.status_code == 200
    r2 = await authed_client.get("/api/v1/onboarding/state")
    assert r2.json()["next_step"] == "subjects"

@pytest.mark.asyncio
async def test_unsupported_subject_rejected(authed_client):
    await authed_client.post("/api/v1/onboarding/education-system", json={"system": "a_level"})
    r = await authed_client.post("/api/v1/onboarding/subjects", json={"subjects": ["physics"]})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_full_flow_to_finalize(authed_client, student):
    await authed_client.post("/api/v1/onboarding/education-system", json={"system": "a_level"})
    await authed_client.post("/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]})
    await authed_client.post("/api/v1/onboarding/exam-board", json={"subject_boards": {"pure_mathematics": "edexcel"}})
    await authed_client.post("/api/v1/onboarding/exam-date", json={"subject_dates": {"pure_mathematics": "2026-11-15"}})
    await authed_client.post("/api/v1/onboarding/target-grade", json={"subject_grades": {"pure_mathematics": {"target": "A*"}}})
    await authed_client.post("/api/v1/onboarding/preferences", json={"worked_examples": True, "step_by_step": False, "visual": False, "practice": True})
    fin = await authed_client.post("/api/v1/onboarding/finalize")
    assert fin.status_code == 200
    assert fin.json()["redirect_to"] == "/dashboard"
```

- [ ] **Step 2: Schemas**

```python
# app/schemas/onboarding.py
from datetime import date
from pydantic import BaseModel, Field
from typing import Literal


class StateOut(BaseModel):
    next_step: Literal["welcome", "education-system", "subjects", "exam-board",
                       "exam-date", "target-grade", "assessment", "preferences",
                       "roadmap", "done"]
    draft: dict


class EducationSystemIn(BaseModel):
    system: Literal["a_level", "gcse", "ib", "university"]


class SubjectsIn(BaseModel):
    subjects: list[str] = Field(..., min_length=1)


class ExamBoardIn(BaseModel):
    subject_boards: dict[str, str]


class ExamDateIn(BaseModel):
    subject_dates: dict[str, str]  # "YYYY-MM-DD" or "unknown"


class GradeForSubject(BaseModel):
    current: str | None = None
    target: Literal["A*", "A", "B", "C", "D", "E"]


class TargetGradeIn(BaseModel):
    subject_grades: dict[str, GradeForSubject]


class PreferencesIn(BaseModel):
    worked_examples: bool = False
    visual: bool = False
    step_by_step: bool = False
    practice: bool = False


class FinalizeOut(BaseModel):
    ok: bool
    redirect_to: str
```

- [ ] **Step 3: Endpoint module**

```python
# app/api/v1/endpoints/onboarding.py
from datetime import date as date_cls, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student
from app.services import learner_profile_service as lps
from app.services.notification_service import emit as emit_notification
from app.schemas.onboarding import (
    StateOut, EducationSystemIn, SubjectsIn, ExamBoardIn, ExamDateIn,
    TargetGradeIn, PreferencesIn, FinalizeOut,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def _wizard_state(student: Student, drafts: list) -> dict:
    """Determine next step from current draft state."""
    if not drafts:
        return {"next_step": "welcome", "draft": {}}
    education_set = any(d.exam_level for d in drafts)
    if not education_set:
        return {"next_step": "education-system", "draft": _draft_dict(drafts)}
    if not any(d.subject for d in drafts):
        return {"next_step": "subjects", "draft": _draft_dict(drafts)}
    if any(not d.exam_board for d in drafts):
        return {"next_step": "exam-board", "draft": _draft_dict(drafts)}
    if any(d.exam_date is None and "explicit_unknown" not in (d.subject or "") for d in drafts):
        return {"next_step": "exam-date", "draft": _draft_dict(drafts)}
    if any(not d.target_grade or d.target_grade == "A" for d in drafts):  # "A" is server default placeholder
        return {"next_step": "target-grade", "draft": _draft_dict(drafts)}
    if not student.preferences:
        return {"next_step": "preferences", "draft": _draft_dict(drafts)}
    if not student.onboarded_at:
        return {"next_step": "roadmap", "draft": _draft_dict(drafts)}
    return {"next_step": "done", "draft": _draft_dict(drafts)}


def _draft_dict(drafts: list) -> dict:
    return {
        "subjects": [
            {
                "subject": d.subject, "exam_board": d.exam_board,
                "exam_level": d.exam_level, "exam_date": d.exam_date.isoformat() if d.exam_date else None,
                "target_grade": d.target_grade, "current_grade": d.current_grade,
            } for d in drafts
        ],
    }


@router.get("/state", response_model=StateOut)
async def get_state(student: Student = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    drafts = await lps.get_or_create_draft(db, student.id)
    return _wizard_state(student, drafts)


@router.post("/education-system")
async def post_system(body: EducationSystemIn, student=Depends(get_current_student), db=Depends(get_db)):
    if body.system != "a_level":
        raise HTTPException(400, "Only A Levels supported")
    # Stash on student.preferences as a transient flag, or create placeholder draft
    student.preferences = {**(student.preferences or {}), "_education_system": body.system}
    await db.flush()
    return {"ok": True}


@router.post("/subjects")
async def post_subjects(body: SubjectsIn, student=Depends(get_current_student), db=Depends(get_db)):
    for subj in body.subjects:
        if not lps.is_supported_combo(subj, "edexcel", "a_level") and not lps.is_supported_combo(subj, "cambridge", "a_level"):
            raise HTTPException(400, f"Subject {subj} not supported")
        await lps.upsert_subject_draft(db, student.id, subj, exam_level="a_level")
    return {"ok": True}


@router.post("/exam-board")
async def post_board(body: ExamBoardIn, student=Depends(get_current_student), db=Depends(get_db)):
    for subj, board in body.subject_boards.items():
        if not lps.is_supported_combo(subj, board, "a_level"):
            raise HTTPException(400, f"{subj} × {board} not supported")
        await lps.upsert_subject_draft(db, student.id, subj, exam_board=board)
    return {"ok": True}


@router.post("/exam-date")
async def post_date(body: ExamDateIn, student=Depends(get_current_student), db=Depends(get_db)):
    for subj, value in body.subject_dates.items():
        exam_date = None if value == "unknown" else date_cls.fromisoformat(value)
        await lps.upsert_subject_draft(db, student.id, subj, exam_date=exam_date)
    return {"ok": True}


@router.post("/target-grade")
async def post_grade(body: TargetGradeIn, student=Depends(get_current_student), db=Depends(get_db)):
    for subj, g in body.subject_grades.items():
        await lps.upsert_subject_draft(db, student.id, subj,
                                       target_grade=g.target, current_grade=g.current)
    return {"ok": True}


@router.post("/preferences")
async def post_prefs(body: PreferencesIn, student=Depends(get_current_student), db=Depends(get_db)):
    await lps.update_preferences(db, student.id, body.model_dump())
    return {"ok": True}


def _compute_minutes(topic_count: int, days: int) -> int:
    if days <= 0: return 90
    raw = (topic_count * 15) // days
    return max(20, min(90, raw))


@router.post("/finalize", response_model=FinalizeOut)
async def finalize(student=Depends(get_current_student), db=Depends(get_db)):
    drafts = await lps.get_or_create_draft(db, student.id)
    if not drafts:
        raise HTTPException(400, "No subjects to finalize")
    # Compute recommended_minutes_per_day per subject
    from app.db.models import SyllabusTopic
    from sqlalchemy import select, func as sa_func
    for d in drafts:
        count = (await db.execute(
            select(sa_func.count(SyllabusTopic.id)).where(
                SyllabusTopic.subject == d.subject, SyllabusTopic.version == d.syllabus_version,
            )
        )).scalar() or 22
        days = (d.exam_date - date_cls.today()).days if d.exam_date else 180
        d.recommended_minutes_per_day = _compute_minutes(count, days)

    await lps.finalize_drafts(db, student.id)
    await emit_notification(db, student.id, "diagnostic_complete",
                           payload={"trigger": "onboarding_finalize"})
    return FinalizeOut(ok=True, redirect_to="/dashboard")
```

- [ ] **Step 4: Wire router; run tests; commit**

In `app/main.py`:
```python
from app.api.v1.endpoints.onboarding import router as onboarding_router
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
```

```bash
pytest tests/test_onboarding_endpoints.py -v
git add app/api/v1/endpoints/onboarding.py app/schemas/onboarding.py app/main.py tests/test_onboarding_endpoints.py
git commit -m "Add onboarding wizard endpoints (server-driven step routing + finalize)"
```

---

### Task 17: Account endpoints

**Files:**
- Create: `app/api/v1/endpoints/account.py`
- Create: `app/schemas/account.py`
- Modify: `app/main.py`
- Create: `tests/test_account_endpoints.py`

**Endpoints:**
- `GET /api/v1/account` → full profile + subjects + preferences + billing tier
- `PATCH /api/v1/account/subjects/{subject_id}` → update subject fields (exam_date, target_grade, etc.)
- `PATCH /api/v1/account/preferences` → update preferences
- `PATCH /api/v1/account/profile` → update name
- (Email update + delete remain placeholders that return 501 / `Contact support`.)

- [ ] **Step 1: Tests**

```python
# tests/test_account_endpoints.py
import pytest

@pytest.mark.asyncio
async def test_get_account_returns_profile(authed_client, student_with_subject):
    r = await authed_client.get("/api/v1/account")
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["name"]
    assert len(body["subjects"]) == 1

@pytest.mark.asyncio
async def test_patch_subject_updates_exam_date(authed_client, student_with_subject):
    sid = student_with_subject.subjects[0].id
    r = await authed_client.patch(f"/api/v1/account/subjects/{sid}",
                                  json={"exam_date": "2027-06-01"})
    assert r.status_code == 200
    assert r.json()["exam_date"] == "2027-06-01"

@pytest.mark.asyncio
async def test_patch_preferences(authed_client, student):
    r = await authed_client.patch("/api/v1/account/preferences",
                                  json={"worked_examples": True, "visual": False, "step_by_step": True, "practice": False})
    assert r.status_code == 200
    assert r.json()["preferences"]["worked_examples"] is True
```

- [ ] **Step 2: Schemas + endpoints**

```python
# app/schemas/account.py
from datetime import date
from pydantic import BaseModel


class ProfileOut(BaseModel):
    name: str
    email: str


class SubjectOut(BaseModel):
    id: str
    subject: str
    exam_board: str
    exam_level: str
    exam_date: date | None
    target_grade: str
    current_grade: str | None
    readiness_pct: float


class PreferencesOut(BaseModel):
    worked_examples: bool = False
    visual: bool = False
    step_by_step: bool = False
    practice: bool = False


class BillingOut(BaseModel):
    tier: str
    status: str


class AccountOut(BaseModel):
    profile: ProfileOut
    subjects: list[SubjectOut]
    preferences: PreferencesOut
    billing: BillingOut


class SubjectPatch(BaseModel):
    exam_date: date | None = None
    target_grade: str | None = None
    current_grade: str | None = None
    exam_board: str | None = None


class ProfilePatch(BaseModel):
    name: str | None = None
```

```python
# app/api/v1/endpoints/account.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student, LearnerSubject
from app.services import learner_profile_service as lps, readiness_service
from app.schemas.account import (
    AccountOut, ProfileOut, SubjectOut, PreferencesOut, BillingOut,
    SubjectPatch, ProfilePatch,
)

router = APIRouter(prefix="/account", tags=["account"])


async def _subject_out(db, ls: LearnerSubject) -> SubjectOut:
    pct = await readiness_service.compute_readiness_pct(db, ls.student_id, ls.subject, ls.syllabus_version)
    return SubjectOut(
        id=str(ls.id), subject=ls.subject, exam_board=ls.exam_board, exam_level=ls.exam_level,
        exam_date=ls.exam_date, target_grade=ls.target_grade, current_grade=ls.current_grade,
        readiness_pct=pct,
    )


@router.get("", response_model=AccountOut)
async def get_account(student: Student = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    subjects = await lps.list_subjects(db, student.id)
    return AccountOut(
        profile=ProfileOut(name=student.name, email=student.email),
        subjects=[await _subject_out(db, s) for s in subjects],
        preferences=PreferencesOut(**{
            k: bool(v) for k, v in (student.preferences or {}).items()
            if k in {"worked_examples", "visual", "step_by_step", "practice"}
        }),
        billing=BillingOut(tier=student.subscription_tier, status=student.subscription_status),
    )


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def patch_subject(subject_id: str, body: SubjectPatch,
                        student=Depends(get_current_student), db=Depends(get_db)):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if "exam_board" in updates and not lps.is_supported_combo(
        (await db.get(LearnerSubject, UUID(subject_id))).subject, updates["exam_board"], "a_level"
    ):
        raise HTTPException(400, "Unsupported board")
    ls = await lps.update_subject(db, student.id, UUID(subject_id), **updates)
    return await _subject_out(db, ls)


@router.patch("/preferences", response_model=AccountOut)
async def patch_preferences(body: dict, student=Depends(get_current_student), db=Depends(get_db)):
    await lps.update_preferences(db, student.id, body)
    return await get_account(student, db)


@router.patch("/profile", response_model=ProfileOut)
async def patch_profile(body: ProfilePatch, student=Depends(get_current_student), db=Depends(get_db)):
    if body.name:
        student.name = body.name.strip()
        await db.flush()
    return ProfileOut(name=student.name, email=student.email)
```

- [ ] **Step 3: Wire, test, commit**

```bash
pytest tests/test_account_endpoints.py -v
git add app/api/v1/endpoints/account.py app/schemas/account.py app/main.py tests/test_account_endpoints.py
git commit -m "Add account endpoints (get, patch subjects/preferences/profile)"
```

---

### Task 18: Notifications endpoints + readyz probe

**Files:**
- Create: `app/api/v1/endpoints/notifications.py`
- Create: `app/schemas/notifications.py`
- Create: `app/api/v1/endpoints/readyz.py`
- Modify: `app/main.py`
- Create: `tests/test_notifications_endpoints.py`
- Create: `tests/test_readyz.py`

**Notifications endpoints:**
- `GET /api/v1/notifications` → `{items: [...], unread_count: int}`
- `POST /api/v1/notifications/mark-read` `{ids: [uuid]}` → `{marked: int}`
- `POST /api/v1/notifications/mark-all-read` → `{marked: int}`

**Readyz:** `GET /readyz` → 200 / 503 per spec §11.

- [ ] **Step 1: Schemas**

```python
# app/schemas/notifications.py
from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    type: str
    payload: dict
    read_at: datetime | None
    created_at: datetime


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class MarkReadIn(BaseModel):
    ids: list[str]
```

- [ ] **Step 2: Endpoints**

```python
# app/api/v1/endpoints/notifications.py
from uuid import UUID
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.services import notification_service as ns
from app.schemas.notifications import NotificationListOut, NotificationOut, MarkReadIn

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
async def list_notifications(student=Depends(get_current_student), db=Depends(get_db)):
    items = await ns.list_recent(db, student.id)
    count = await ns.unread_count(db, student.id)
    return NotificationListOut(
        items=[NotificationOut(id=str(n.id), type=n.type, payload=n.payload,
                               read_at=n.read_at, created_at=n.created_at) for n in items],
        unread_count=count,
    )


@router.post("/mark-read")
async def mark_read(body: MarkReadIn, student=Depends(get_current_student), db=Depends(get_db)):
    n = await ns.mark_read(db, student.id, [UUID(i) for i in body.ids])
    return {"marked": n}


@router.post("/mark-all-read")
async def mark_all_read(student=Depends(get_current_student), db=Depends(get_db)):
    n = await ns.mark_all_read(db, student.id)
    return {"marked": n}
```

```python
# app/api/v1/endpoints/readyz.py
from fastapi import APIRouter, HTTPException
import os
from sqlalchemy import select, func
from app.db.database import async_session_maker
from app.db.models import SyllabusTopic
from app.core.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/readyz")
async def readyz():
    failures = []
    # DB
    try:
        async with async_session_maker() as db:
            res = await db.execute(
                select(func.count(SyllabusTopic.id)).where(
                    SyllabusTopic.version == "2026.1"
                )
            )
            if (res.scalar() or 0) == 0:
                failures.append("no_syllabus_topics")
    except Exception as e:
        failures.append(f"db: {e}")
    # Redis
    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        failures.append(f"redis: {e}")
    # LLM key
    if not os.environ.get("GROQ_API_KEY"):
        failures.append("groq_api_key_missing")

    if failures:
        raise HTTPException(503, {"status": "not_ready", "failures": failures})
    return {"status": "ready"}
```

- [ ] **Step 3: Tests, wire, commit**

```python
# tests/test_readyz.py
import pytest

@pytest.mark.asyncio
async def test_readyz_503_when_no_syllabus(unauth_client, empty_db):
    r = await unauth_client.get("/readyz")
    assert r.status_code == 503

@pytest.mark.asyncio
async def test_readyz_200_when_seeded(unauth_client, syllabus_edexcel_seeded):
    r = await unauth_client.get("/readyz")
    assert r.status_code == 200
```

In `app/main.py`:
```python
from app.api.v1.endpoints.notifications import router as notif_router
from app.api.v1.endpoints.readyz import router as readyz_router
app.include_router(notif_router, prefix=settings.api_v1_prefix)
app.include_router(readyz_router)  # no api prefix
```

```bash
pytest tests/test_notifications_endpoints.py tests/test_readyz.py -v
git add app/api/v1/endpoints/notifications.py app/api/v1/endpoints/readyz.py \
        app/schemas/notifications.py app/main.py \
        tests/test_notifications_endpoints.py tests/test_readyz.py
git commit -m "Add notifications endpoints and /readyz readiness probe"
```

---

### Task 19: Admin inspect endpoint

**Files:**
- Modify: `app/api/v1/endpoints/admin.py` (add `/students/{id}/inspect`)
- Create: `app/schemas/admin.py`
- Create: `tests/test_admin_inspect.py`

**Endpoint:** `GET /api/v1/admin/students/{student_id}/inspect` → JSON blob with learner profile, all subjects, mastery, latest today_focus, active session, last 7 session summaries.

**Gating:** require `current_student.is_admin == True`.

- [ ] **Step 1: Tests**

```python
# tests/test_admin_inspect.py
import pytest

@pytest.mark.asyncio
async def test_inspect_requires_admin(authed_client, student_with_subject):
    r = await authed_client.get(f"/api/v1/admin/students/{student_with_subject.id}/inspect")
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_inspect(admin_authed_client, student_with_subject):
    r = await admin_authed_client.get(f"/api/v1/admin/students/{student_with_subject.id}/inspect")
    assert r.status_code == 200
    body = r.json()
    assert "profile" in body
    assert "subjects" in body
    assert "mastery" in body
```

- [ ] **Step 2: Implementation**

In `app/api/v1/endpoints/admin.py`, add:

```python
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy import select
from app.db.models import Student, LearnerSubject, MasteryState, TutorSession, TodayFocusHistory
from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db


def require_admin(student: Student = Depends(get_current_student)) -> Student:
    if not student.is_admin:
        raise HTTPException(403, "Admin only")
    return student


@router.get("/students/{student_id}/inspect")
async def inspect_student(student_id: str, admin=Depends(require_admin), db=Depends(get_db)):
    target = await db.get(Student, UUID(student_id))
    if not target:
        raise HTTPException(404, "Student not found")

    subjects = (await db.execute(
        select(LearnerSubject).where(LearnerSubject.student_id == target.id)
    )).scalars().all()
    mastery = (await db.execute(
        select(MasteryState).where(MasteryState.student_id == target.id)
    )).scalars().all()
    latest_focus = (await db.execute(
        select(TodayFocusHistory).where(TodayFocusHistory.student_id == target.id)
        .order_by(TodayFocusHistory.focus_date.desc()).limit(1)
    )).scalar_one_or_none()
    active = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == target.id,
            TutorSession.ended_at.is_(None),
        ).order_by(TutorSession.started_at.desc()).limit(1)
    )).scalar_one_or_none()
    recent_sessions = (await db.execute(
        select(TutorSession).where(
            TutorSession.student_id == target.id,
        ).order_by(TutorSession.started_at.desc()).limit(7)
    )).scalars().all()

    return {
        "profile": {
            "id": str(target.id), "name": target.name, "email": target.email,
            "onboarded_at": target.onboarded_at, "subscription_tier": target.subscription_tier,
            "preferences": target.preferences,
        },
        "subjects": [
            {"id": str(s.id), "subject": s.subject, "exam_board": s.exam_board,
             "exam_date": s.exam_date, "target_grade": s.target_grade,
             "syllabus_version": s.syllabus_version, "is_draft": s.is_draft}
            for s in subjects
        ],
        "mastery": [
            {"topic": m.topic, "mastery_score": m.mastery_score,
             "total_attempts": m.total_attempts, "is_weak": m.is_weak}
            for m in mastery
        ],
        "latest_today_focus": {
            "focus_date": latest_focus.focus_date,
            "shape": latest_focus.shape,
            "segment_plan": latest_focus.segment_plan,
            "reasoning": latest_focus.reasoning,
        } if latest_focus else None,
        "active_session": {
            "id": str(active.id), "session_type": active.session_type,
            "session_version": active.session_version,
            "segment_plan": active.segment_plan,
            "current_segment_idx": active.current_segment_idx,
            "started_at": active.started_at,
        } if active else None,
        "recent_sessions": [
            {"id": str(s.id), "subject": s.subject, "topic": s.topic,
             "started_at": s.started_at, "ended_at": s.ended_at,
             "session_type": s.session_type}
            for s in recent_sessions
        ],
    }
```

- [ ] **Step 3: Add `admin_authed_client` fixture, run, commit**

In `tests/conftest.py`:
```python
@pytest.fixture
async def admin_student(db_session):
    from app.db.models import Student
    s = Student(email="admin@test", name="Admin", hashed_password="x", is_admin=True)
    db_session.add(s); await db_session.flush()
    return s

@pytest.fixture
async def admin_authed_client(client, admin_student):
    # Reuse the auth flow used by `authed_client` but with admin_student
    ...
```

```bash
pytest tests/test_admin_inspect.py -v
git add app/api/v1/endpoints/admin.py tests/test_admin_inspect.py tests/conftest.py
git commit -m "Add admin /students/{id}/inspect endpoint for debugging"
```

---

## Phase F — Frontend Foundation (3 tasks)

### Task 20: PostHog feature-flag client hook + wrapper

**Files:**
- Create: `web/src/lib/feature-flags.ts`
- Create: `web/src/components/shell/feature-flag.tsx`
- Create: `web/src/lib/__tests__/feature-flags.test.ts` (if vitest configured; else inline manual QA)

**Interfaces produced:**
- `useFeatureFlag(name: string, defaultValue?: boolean): boolean`
- `<FeatureFlag flag="dashboard_v2" fallback={<LegacyDashboard/>}>{children}</FeatureFlag>`

- [ ] **Step 1: Implement hook**

```typescript
// web/src/lib/feature-flags.ts
"use client";
import { useEffect, useState } from "react";
import posthog from "posthog-js";

export type StrideFlag =
  | "dashboard_v2"
  | "onboarding_v2"
  | "session_engine_v2"
  | "notifications_v2"
  | "account_v2";

const KNOWN_FLAGS: ReadonlyArray<StrideFlag> = [
  "dashboard_v2", "onboarding_v2", "session_engine_v2", "notifications_v2", "account_v2",
];

export function useFeatureFlag(flag: StrideFlag, defaultValue = true): boolean {
  const [enabled, setEnabled] = useState<boolean>(defaultValue);

  useEffect(() => {
    if (!KNOWN_FLAGS.includes(flag)) return;
    const update = () => {
      const v = posthog.isFeatureEnabled(flag);
      setEnabled(v === undefined ? defaultValue : !!v);
    };
    update();
    posthog.onFeatureFlags(update);
  }, [flag, defaultValue]);

  return enabled;
}
```

- [ ] **Step 2: Wrapper component**

```tsx
// web/src/components/shell/feature-flag.tsx
"use client";
import { ReactNode } from "react";
import { useFeatureFlag, StrideFlag } from "@/lib/feature-flags";

interface Props {
  flag: StrideFlag;
  fallback?: ReactNode;
  children: ReactNode;
}

export function FeatureFlag({ flag, fallback = null, children }: Props) {
  const enabled = useFeatureFlag(flag, true);
  return <>{enabled ? children : fallback}</>;
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/feature-flags.ts web/src/components/shell/feature-flag.tsx
git commit -m "Add PostHog feature-flag client hook + FeatureFlag wrapper component"
```

---

### Task 21: API client modules (typed)

**Files:**
- Create: `web/src/lib/api/onboarding.ts`
- Create: `web/src/lib/api/dashboard.ts`
- Create: `web/src/lib/api/account.ts`
- Create: `web/src/lib/api/notifications.ts`
- Modify: `web/src/lib/types.ts` (add types matching backend Pydantic schemas)

**Interfaces produced:**
- `onboardingApi.getState(): Promise<OnboardingState>`
- `onboardingApi.submitStep(step, body)` — one method per step
- `dashboardApi.get(subject: string): Promise<DashboardPayload>`
- `accountApi.get(): Promise<AccountPayload>`
- `accountApi.patchSubject(subjectId, body)`
- `accountApi.patchPreferences(body)`
- `notificationsApi.list(): Promise<{items, unread_count}>`
- `notificationsApi.markRead(ids)` / `markAllRead()`

- [ ] **Step 1: Add types**

In `web/src/lib/types.ts`, append types mirroring backend Pydantic models (DashboardPayload, OnboardingState, AccountPayload, NotificationOut, etc.). Each maps exactly to the backend response shape from Phases D/E.

- [ ] **Step 2: Implement clients**

Each module follows the same shape — wrap `fetch` with the existing auth header injection from `web/src/lib/api.ts`. Example:

```typescript
// web/src/lib/api/dashboard.ts
import { apiFetch } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";

export const dashboardApi = {
  get: (subject: string) => apiFetch<DashboardPayload>(`/dashboard/${subject}`),
};
```

Repeat for onboarding, account, notifications with their respective endpoints.

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/api/ web/src/lib/types.ts
git commit -m "Add typed API client modules for onboarding/dashboard/account/notifications"
```

---

### Task 22: Shell — top bar + avatar menu + notification bell

**Files:**
- Modify: `web/src/app/(app)/layout.tsx`
- Create: `web/src/components/shell/top-bar.tsx`
- Create: `web/src/components/shell/avatar-menu.tsx`
- Create: `web/src/components/shell/notification-bell.tsx`
- Delete contents of: `web/src/app/(app)/progress/page.tsx` → replace with 410 redirect

**Behavior:** logo (left, links to `/dashboard`), spacer, notification bell (right), avatar menu (right). On `/session/[id]/*`, shell chrome hidden via `usePathname` check.

- [ ] **Step 1: Top bar**

```tsx
// web/src/components/shell/top-bar.tsx
"use client";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { NotificationBell } from "./notification-bell";
import { AvatarMenu } from "./avatar-menu";

export function TopBar({ studentName }: { studentName: string }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[var(--border)] bg-white px-4">
      <Link href="/dashboard" className="flex items-center gap-2">
        <Logo />
        <span className="font-semibold">Stride</span>
      </Link>
      <div className="flex items-center gap-3">
        <NotificationBell />
        <AvatarMenu name={studentName} />
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Avatar menu (Account · Sign out)**

```tsx
// web/src/components/shell/avatar-menu.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "@/lib/auth";

export function AvatarMenu({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const initial = name?.[0]?.toUpperCase() ?? "?";
  return (
    <div className="relative">
      <button onClick={() => setOpen(v => !v)}
        className="grid h-8 w-8 place-items-center rounded-full bg-[var(--blue)] text-white">
        {initial}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-44 rounded-md border border-[var(--border)] bg-white py-1 shadow-lg">
          <button className="block w-full px-3 py-2 text-left hover:bg-gray-50"
            onClick={() => { setOpen(false); router.push("/account"); }}>Account</button>
          <button className="block w-full px-3 py-2 text-left hover:bg-gray-50"
            onClick={async () => { await signOut(); router.push("/login"); }}>Sign out</button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Notification bell**

```tsx
// web/src/components/shell/notification-bell.tsx
"use client";
import { useEffect, useState } from "react";
import { notificationsApi } from "@/lib/api/notifications";
import { useFeatureFlag } from "@/lib/feature-flags";

export function NotificationBell() {
  const enabled = useFeatureFlag("notifications_v2", true);
  const [unread, setUnread] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    if (!enabled) return;
    notificationsApi.list().then(r => { setUnread(r.unread_count); setItems(r.items); }).catch(() => setUnread(null));
  }, [enabled, open]);

  if (!enabled) return null;

  return (
    <div className="relative">
      <button onClick={() => setOpen(v => !v)} className="relative p-2">
        <BellIcon />
        {unread != null && unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] text-white">{unread > 9 ? "9+" : unread}</span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-md border border-[var(--border)] bg-white shadow-lg">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <h3 className="font-semibold">Notifications</h3>
            <button className="text-xs text-[var(--blue)]" onClick={async () => {
              await notificationsApi.markAllRead(); setUnread(0);
            }}>Mark all read</button>
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {items.length === 0
              ? <li className="px-3 py-6 text-center text-sm text-[var(--text-secondary)]">No notifications yet.</li>
              : items.map(n => (
                  <li key={n.id} className={`border-b px-3 py-2 text-sm ${!n.read_at ? "bg-blue-50" : ""}`}>
                    {labelFor(n)}
                  </li>
                ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function labelFor(n: { type: string; payload: any }): string {
  switch (n.type) {
    case "readiness_increased": return `Your readiness increased by ${n.payload.delta}%`;
    case "diagnostic_complete": return "Your diagnostic is ready — view your roadmap";
    case "subscription_renewed": return "Your Pro subscription renewed";
    case "session_reminder": return n.payload.message || "Time for today's session";
    default: return n.type;
  }
}

function BellIcon() {
  return <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>;
}
```

- [ ] **Step 4: Update app layout to use TopBar; hide on session routes**

```tsx
// web/src/app/(app)/layout.tsx
"use client";
import { usePathname } from "next/navigation";
import { TopBar } from "@/components/shell/top-bar";
import { useStudent } from "@/lib/auth";  // existing hook

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const student = useStudent();
  const inSession = pathname?.startsWith("/session/");
  return (
    <div className="min-h-screen bg-[var(--bg)]">
      {!inSession && student && <TopBar studentName={student.name} />}
      <main className={inSession ? "" : "mx-auto max-w-3xl px-4 py-6"}>{children}</main>
    </div>
  );
}
```

- [ ] **Step 5: Replace `/progress` with redirect**

```tsx
// web/src/app/(app)/progress/page.tsx
import { redirect } from "next/navigation";
export default function ProgressRedirect() {
  redirect("/dashboard");
}
```

- [ ] **Step 6: Commit**

```bash
git add web/src/components/shell/ web/src/app/(app)/layout.tsx web/src/app/(app)/progress/page.tsx
git commit -m "Add new shell (top bar, avatar menu, notification bell); redirect /progress to /dashboard"
```

---

## Phase G — Onboarding Frontend (3 tasks)

### Task 23: Wizard shell + shared form field components

**Files:**
- Create: `web/src/components/onboarding/wizard-shell.tsx`
- Create: `web/src/components/onboarding/fields/system-picker.tsx`
- Create: `web/src/components/onboarding/fields/subject-picker.tsx`
- Create: `web/src/components/onboarding/fields/board-picker.tsx`
- Create: `web/src/components/onboarding/fields/exam-date-picker.tsx`
- Create: `web/src/components/onboarding/fields/grade-picker.tsx`
- Modify: `web/src/app/(onboarding)/onboarding/layout.tsx` (wrap children in wizard-shell)

**Behavior:** wizard-shell shows progress dots at top + back button. Each field component:
- Renders all options (supported + "Coming soon") with disabled state for the latter
- Tooltip on hover for disabled
- Validates locally, then submits via API client

- [ ] **Step 1: Wizard shell**

```tsx
// web/src/components/onboarding/wizard-shell.tsx
"use client";
import { ReactNode } from "react";
import { useRouter } from "next/navigation";

const STEPS = ["welcome","education-system","subjects","exam-board","exam-date","target-grade","assessment","preferences","roadmap"] as const;
type Step = typeof STEPS[number];

export function WizardShell({ step, children }: { step: Step; children: ReactNode }) {
  const router = useRouter();
  const idx = STEPS.indexOf(step);
  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <div className="mb-6 flex items-center gap-2">
        {STEPS.map((s, i) => (
          <span key={s} className={`h-1.5 flex-1 rounded ${i <= idx ? "bg-[var(--blue)]" : "bg-gray-200"}`} />
        ))}
      </div>
      {idx > 0 && idx < STEPS.length - 1 && (
        <button onClick={() => router.back()} className="mb-4 text-sm text-[var(--text-secondary)]">← Back</button>
      )}
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Subject picker (representative pattern; others follow same shape)**

```tsx
// web/src/components/onboarding/fields/subject-picker.tsx
"use client";
import { useState } from "react";

const SUBJECTS = [
  { id: "pure_mathematics", label: "Pure Mathematics", supported: true },
  { id: "mechanics_statistics", label: "Mechanics & Statistics", supported: false },
  { id: "physics", label: "Physics", supported: false },
  { id: "chemistry", label: "Chemistry", supported: false },
];

export function SubjectPicker({ initial = [], onChange }: { initial?: string[]; onChange: (s: string[]) => void }) {
  const [selected, setSelected] = useState<string[]>(initial);
  const toggle = (id: string) => {
    const next = selected.includes(id) ? selected.filter(s => s !== id) : [...selected, id];
    setSelected(next); onChange(next);
  };
  return (
    <div className="grid gap-2">
      {SUBJECTS.map(s => (
        <button key={s.id} disabled={!s.supported} onClick={() => toggle(s.id)}
          title={!s.supported ? "Coming soon" : ""}
          className={`flex items-center justify-between rounded-lg border p-3 text-left
            ${selected.includes(s.id) ? "border-[var(--blue)] bg-blue-50" : "border-[var(--border)]"}
            ${!s.supported ? "cursor-not-allowed opacity-50" : "hover:border-[var(--blue)]"}`}>
          <span>{s.label}</span>
          {!s.supported && <span className="text-xs text-[var(--text-secondary)]">Coming soon</span>}
        </button>
      ))}
    </div>
  );
}
```

Repeat the same disabled-with-tooltip pattern for `system-picker`, `board-picker`, `grade-picker`. `exam-date-picker` is a native `<input type="date">` plus a "Don't know yet" checkbox.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/onboarding/
git commit -m "Add onboarding wizard shell and shared field components"
```

---

### Task 24: Onboarding steps — welcome through preferences

**Files:**
- Modify: `web/src/app/(onboarding)/onboarding/page.tsx` (redirect to `/onboarding/welcome`)
- Modify: `web/src/app/(onboarding)/onboarding/welcome/page.tsx`
- Create one page per wizard step (7 new pages)

**Pattern (same shape across all step pages):** server-side reads `/onboarding/state`, renders the step component (WizardShell + field components), on submit POSTs to the relevant endpoint, redirects to `next_step` returned by re-fetched state.

- [ ] **Step 1: Welcome page**

```tsx
// web/src/app/(onboarding)/onboarding/welcome/page.tsx
"use client";
import Link from "next/link";
import { WizardShell } from "@/components/onboarding/wizard-shell";

export default function WelcomePage() {
  return (
    <WizardShell step="welcome">
      <h1 className="mb-3 text-3xl font-semibold">Meet Alex, your AI exam coach.</h1>
      <p className="mb-8 text-[var(--text-secondary)]">Stride will create a personalised study plan based on your subjects, goals, and current ability.</p>
      <Link href="/onboarding/education-system"
        className="inline-block rounded-lg bg-[var(--blue)] px-5 py-3 text-white">Get started</Link>
    </WizardShell>
  );
}
```

- [ ] **Step 2: Subjects page (representative; other field steps follow same shape)**

```tsx
// web/src/app/(onboarding)/onboarding/subjects/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { SubjectPicker } from "@/components/onboarding/fields/subject-picker";
import { onboardingApi } from "@/lib/api/onboarding";

export default function SubjectsStep() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<string[]>([]);
  return (
    <WizardShell step="subjects">
      <h1 className="mb-2 text-2xl font-semibold">Which subjects?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">Pick the subjects you're studying.</p>
      <SubjectPicker onChange={setSubjects} />
      <button disabled={subjects.length === 0}
        onClick={async () => {
          await onboardingApi.submitSubjects({ subjects });
          const state = await onboardingApi.getState();
          router.push(`/onboarding/${state.next_step}`);
        }}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50">
        Continue
      </button>
    </WizardShell>
  );
}
```

- [ ] **Step 3: Repeat the same pattern for `education-system`, `exam-board`, `exam-date`, `target-grade`, `preferences`**

Each page: a heading, the relevant field component, a Continue button that POSTs to the right endpoint and routes to `next_step`. The pages differ only in (a) which field component is rendered, (b) which API method is called, (c) the heading copy. Keep all 5 pages thin — heavy lifting lives in the field components and the API client.

- [ ] **Step 4: Commit**

```bash
git add web/src/app/(onboarding)/onboarding/
git commit -m "Add onboarding wizard pages (welcome through preferences)"
```

---

### Task 25: Onboarding assessment + roadmap steps

**Files:**
- Create: `web/src/app/(onboarding)/onboarding/assessment/page.tsx`
- Create: `web/src/app/(onboarding)/onboarding/roadmap/page.tsx`

**Assessment page:** two cards (Take diagnostic / Skip). Diagnostic launches a `session_type=diagnostic` session via `POST /api/v1/sessions/start` and redirects to `/session/{id}`; on session completion the existing session-end handler redirects back to `/onboarding/preferences` (next step). Skip just routes forward.

**Roadmap page:** fetches `/api/v1/dashboard/{subject}` for a preview, shows readiness/days/recommended_minutes/top topics, button calls `/api/v1/onboarding/finalize` then routes to `/dashboard`.

- [ ] **Step 1: Assessment page**

```tsx
// web/src/app/(onboarding)/onboarding/assessment/page.tsx
"use client";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { apiFetch } from "@/lib/api";
import { onboardingApi } from "@/lib/api/onboarding";

export default function AssessmentStep() {
  const router = useRouter();
  const skip = async () => {
    const s = await onboardingApi.getState();
    router.push(`/onboarding/${s.next_step}`);
  };
  const takeDiagnostic = async () => {
    const session = await apiFetch<{ id: string }>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject: "pure_mathematics", session_type: "diagnostic",
                             return_to: "/onboarding/preferences" }),
    });
    router.push(`/session/${session.id}`);
  };
  return (
    <WizardShell step="assessment">
      <h1 className="mb-6 text-2xl font-semibold">Let's get a baseline.</h1>
      <div className="grid gap-3">
        <button onClick={takeDiagnostic}
          className="rounded-lg border border-[var(--blue)] bg-blue-50 p-4 text-left">
          <div className="font-semibold">Take a 10-minute diagnostic</div>
          <div className="text-sm text-[var(--text-secondary)]">Recommended — gives Alex a real picture of where you are.</div>
        </button>
        <button onClick={skip}
          className="rounded-lg border border-[var(--border)] p-4 text-left">
          <div className="font-semibold">Skip for now</div>
          <div className="text-sm text-[var(--text-secondary)]">Alex will calibrate during your first session.</div>
        </button>
      </div>
    </WizardShell>
  );
}
```

- [ ] **Step 2: Roadmap page**

```tsx
// web/src/app/(onboarding)/onboarding/roadmap/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { dashboardApi } from "@/lib/api/dashboard";
import { onboardingApi } from "@/lib/api/onboarding";

export default function RoadmapStep() {
  const router = useRouter();
  const [data, setData] = useState<any | null>(null);
  useEffect(() => {
    dashboardApi.get("pure_mathematics").then(setData);
  }, []);
  if (!data) return <WizardShell step="roadmap"><p>Building your roadmap…</p></WizardShell>;
  return (
    <WizardShell step="roadmap">
      <h1 className="mb-2 text-2xl font-semibold">Your exam roadmap is ready.</h1>
      <dl className="my-6 grid grid-cols-2 gap-4">
        <div><dt className="text-sm text-[var(--text-secondary)]">Readiness</dt><dd className="text-2xl font-semibold">{Math.round(data.readiness_pct)}%</dd></div>
        <div><dt className="text-sm text-[var(--text-secondary)]">Target</dt><dd className="text-2xl font-semibold">{data.target_grade}</dd></div>
        <div><dt className="text-sm text-[var(--text-secondary)]">Days remaining</dt><dd className="text-2xl font-semibold">{data.days_until_exam ?? "—"}</dd></div>
        <div><dt className="text-sm text-[var(--text-secondary)]">Recommended study</dt><dd className="text-2xl font-semibold">{/* derived elsewhere */}25 min/day</dd></div>
      </dl>
      {data.weak_topics?.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Priority topics</h2>
          <ul className="grid gap-1 text-sm">
            {data.weak_topics.slice(0, 3).map((t: any, i: number) => (
              <li key={t.topic}>{i + 1}. {t.topic_name}</li>
            ))}
          </ul>
        </div>
      )}
      <button onClick={async () => {
        await onboardingApi.finalize();
        router.push("/dashboard");
      }} className="rounded-lg bg-[var(--blue)] px-5 py-3 text-white">
        Start your first session
      </button>
    </WizardShell>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/app/(onboarding)/onboarding/assessment/ web/src/app/(onboarding)/onboarding/roadmap/
git commit -m "Add onboarding assessment and roadmap steps"
```

---

## Phase H — Dashboard Frontend (3 tasks)

### Task 26: Dashboard page skeleton + countdown band + readiness card

**Files:**
- Modify: `web/src/app/(app)/dashboard/page.tsx`
- Create: `web/src/components/dashboard/countdown-band.tsx`
- Create: `web/src/components/dashboard/readiness-card.tsx`
- Create: `web/src/components/dashboard/subject-switcher.tsx`

- [ ] **Step 1: Dashboard page (data loading + composition)**

```tsx
// web/src/app/(app)/dashboard/page.tsx
"use client";
import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/api/dashboard";
import { useFeatureFlag } from "@/lib/feature-flags";
import { LegacyDashboard } from "./_legacy";  // keep old impl moved here in this task
import { SubjectSwitcher } from "@/components/dashboard/subject-switcher";
import { CountdownBand } from "@/components/dashboard/countdown-band";
import { ReadinessCard } from "@/components/dashboard/readiness-card";
import { ResumeSessionCard } from "@/components/dashboard/resume-session-card";
import { TodayFocusCard } from "@/components/dashboard/today-focus-card";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { TopicsList } from "@/components/dashboard/topics-list";

export default function DashboardPage() {
  const v2 = useFeatureFlag("dashboard_v2", true);
  if (!v2) return <LegacyDashboard />;

  const [subject, setSubject] = useState("pure_mathematics");
  const [data, setData] = useState<any | null>(null);
  useEffect(() => {
    dashboardApi.get(subject).then(setData);
  }, [subject]);
  if (!data) return <p className="p-6">Loading…</p>;
  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Good morning, {/* name from useStudent */}.</h1>
        {data.subject_options?.length > 1 && (
          <SubjectSwitcher current={subject} options={data.subject_options} onChange={setSubject} />
        )}
      </header>
      <CountdownBand data={data} />
      <ReadinessCard data={data} />
      {data.resume_session && <ResumeSessionCard data={data.resume_session} />}
      {!data.resume_session && <TodayFocusCard data={data.today_focus} />}
      {data.recent_activity && <RecentActivity data={data.recent_activity} />}
      <TopicsList strong={data.strong_topics} weak={data.weak_topics} />
    </div>
  );
}
```

Before rewriting, copy the existing `dashboard/page.tsx` contents to `dashboard/_legacy.tsx` exported as `LegacyDashboard`.

- [ ] **Step 2: Countdown band**

```tsx
// web/src/components/dashboard/countdown-band.tsx
import Link from "next/link";

export function CountdownBand({ data }: { data: any }) {
  const days = data.days_until_exam;
  const dateLabel = (() => {
    if (days === null || days === undefined) return "Estimated: ~6 months";
    if (days < 0) return "Exam has passed";
    if (days > 365) return "1 year+ until exam";
    return `Pure Maths exam — ${days} days remaining`;
  })();
  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-4">
      <p className="text-sm text-[var(--text-secondary)]">{dateLabel}{days < 0 && <Link href="/account#academic" className="ml-2 text-[var(--blue)]">Set a new date →</Link>}</p>
      <div className="mt-2 flex items-center gap-6">
        <div><dt className="text-xs text-[var(--text-secondary)]">Target</dt><dd className="text-lg font-semibold">{data.target_grade}</dd></div>
        {data.predicted_grade && (
          <div><dt className="text-xs text-[var(--text-secondary)]">Current prediction</dt><dd className="text-lg font-semibold">{data.predicted_grade}<span className="ml-1 text-xs font-normal text-[var(--text-secondary)]">est.</span></dd></div>
        )}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Readiness card**

```tsx
// web/src/components/dashboard/readiness-card.tsx
export function ReadinessCard({ data }: { data: any }) {
  const pct = Math.round(data.readiness_pct);
  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <h2 className="mb-2 text-xs uppercase tracking-wide text-[var(--text-secondary)]">Exam Readiness</h2>
      <div className="text-4xl font-semibold">{pct}%</div>
      <div className="mt-3 h-2 overflow-hidden rounded bg-gray-100">
        <div className="h-full bg-[var(--blue)]" style={{ width: `${pct}%` }} />
      </div>
      {data.readiness_trend ? (
        <p className="mt-3 text-sm text-[var(--blue)]">
          {data.readiness_trend.delta >= 0 ? "+" : ""}{data.readiness_trend.delta}% this month
        </p>
      ) : (
        <p className="mt-3 text-sm text-[var(--text-secondary)]">
          You're just getting started — complete a few study sessions and we'll begin tracking your improvement over time.
        </p>
      )}
    </section>
  );
}
```

- [ ] **Step 4: Subject switcher**

Simple `<select>` controlled component. Skip code body — direct render of `data.subject_options.map`, calling `onChange`.

- [ ] **Step 5: Commit**

```bash
git add web/src/app/(app)/dashboard/ web/src/components/dashboard/countdown-band.tsx web/src/components/dashboard/readiness-card.tsx web/src/components/dashboard/subject-switcher.tsx
git commit -m "Add dashboard page skeleton with countdown band and readiness card (flag-gated)"
```

---

### Task 27: Resume Session card + Today's Focus card + Recent Activity

**Files:**
- Create: `web/src/components/dashboard/resume-session-card.tsx`
- Create: `web/src/components/dashboard/today-focus-card.tsx`
- Create: `web/src/components/dashboard/recent-activity.tsx`

- [ ] **Step 1: Resume Session card**

```tsx
// web/src/components/dashboard/resume-session-card.tsx
import Link from "next/link";

export function ResumeSessionCard({ data }: { data: { session_id: string; completed_segments: number; total_segments: number } }) {
  return (
    <section className="rounded-lg border border-[var(--blue)] bg-blue-50 p-5">
      <h2 className="text-lg font-semibold">Resume today's session</h2>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">Completed: {data.completed_segments} / {data.total_segments} segments</p>
      <Link href={`/session/${data.session_id}`}
        className="mt-3 inline-block rounded-lg bg-[var(--blue)] px-4 py-2 text-white">
        Continue
      </Link>
    </section>
  );
}
```

- [ ] **Step 2: Today's Focus card with progress dots**

```tsx
// web/src/components/dashboard/today-focus-card.tsx
"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";

export function TodayFocusCard({ data }: { data: any }) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);
  const start = async () => {
    setStarting(true);
    const s = await apiFetch<{ id: string }>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject: "pure_mathematics", session_type: "practice",
                             segment_plan: data.segment_plan }),
    });
    router.push(`/session/${s.id}`);
  };
  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <header className="mb-4">
        <h2 className="text-lg font-semibold">Today's Session · {data.total_minutes} min</h2>
        <p className="text-sm text-[var(--text-secondary)]">Complete these three activities to stay on track for your target grade.</p>
      </header>
      <ol className="space-y-3">
        {data.segment_plan.map((s: any) => (
          <li key={s.idx} className="flex items-start gap-3">
            <span className={`mt-1 grid h-5 w-5 place-items-center rounded-full text-[10px]
              ${s.status === "done" ? "bg-[var(--blue)] text-white" :
                s.status === "in_progress" ? "bg-[var(--blue)] text-white" : "border border-gray-300"}`}>
              {s.status === "done" ? "✓" : s.idx + 1}
            </span>
            <div>
              <div className="font-medium">{titleFor(s)} · {s.target_minutes} min</div>
              <div className="text-sm text-[var(--text-secondary)]">{s.why}</div>
            </div>
          </li>
        ))}
      </ol>
      <button onClick={start} disabled={starting}
        className="mt-5 w-full rounded-lg bg-[var(--blue)] px-4 py-3 text-white disabled:opacity-50">
        {starting ? "Starting…" : "Start session"}
      </button>
    </section>
  );
}

function titleFor(s: any): string {
  const intent = s.intent[0].toUpperCase() + s.intent.slice(1);
  if (s.topic) return `${intent} ${s.topic.replace(/_/g, " ")}`;
  return intent;
}
```

- [ ] **Step 3: Recent Activity row**

```tsx
// web/src/components/dashboard/recent-activity.tsx
export function RecentActivity({ data }: { data: { last_studied: string | null; summary: string | null; cold: boolean } }) {
  if (data.cold) {
    return <p className="text-sm text-[var(--text-secondary)]">You haven't studied in a few days. Let's get back on track.</p>;
  }
  if (!data.last_studied) return null;
  return <p className="text-sm text-[var(--text-secondary)]">Last studied: {data.last_studied} · {data.summary}</p>;
}
```

- [ ] **Step 4: Commit**

```bash
git add web/src/components/dashboard/
git commit -m "Add Today's Focus card with progress dots, Resume card, Recent Activity"
```

---

### Task 28: Strong / Weak topics list

**Files:**
- Create: `web/src/components/dashboard/topics-list.tsx`

- [ ] **Step 1: Component**

```tsx
// web/src/components/dashboard/topics-list.tsx
export function TopicsList({ strong, weak }: { strong: any[]; weak: any[] }) {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Strong</h3>
        <ul className="space-y-1 text-sm">
          {strong.length === 0
            ? <li className="text-[var(--text-secondary)]">Nothing yet — keep practising.</li>
            : strong.map(t => <li key={t.topic}>✓ {t.topic_name} · {t.mastery_pct}%</li>)}
        </ul>
      </div>
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Needs work</h3>
        <ul className="space-y-1 text-sm">
          {weak.length === 0
            ? <li className="text-[var(--text-secondary)]">All clear for now.</li>
            : weak.map(t => <li key={t.topic}>⚠ {t.topic_name} · {t.mastery_pct}%</li>)}
        </ul>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/components/dashboard/topics-list.tsx
git commit -m "Add strong/weak topics list"
```

---

## Phase I — Session Frontend (1 task)

### Task 29: Full-screen session takeover + smart exit + segment progress

**Files:**
- Modify: `web/src/app/(app)/session/[id]/page.tsx`
- Create: `web/src/components/session/exit-confirmation.tsx`
- Create: `web/src/components/session/segment-progress.tsx`

- [ ] **Step 1: Segment progress bar**

```tsx
// web/src/components/session/segment-progress.tsx
export function SegmentProgress({ plan, currentIdx }: { plan: any[]; currentIdx: number }) {
  return (
    <ol className="flex items-center gap-2">
      {plan.map((s, i) => (
        <li key={s.idx} className="flex items-center gap-2">
          <span className={`grid h-5 w-5 place-items-center rounded-full text-[10px]
            ${i < currentIdx ? "bg-[var(--blue)] text-white"
              : i === currentIdx ? "border-2 border-[var(--blue)]"
              : "border border-gray-300"}`}>
            {i < currentIdx ? "✓" : i + 1}
          </span>
          <span className="text-xs text-[var(--text-secondary)]">{s.intent}</span>
          {i < plan.length - 1 && <span className="text-gray-300">·</span>}
        </li>
      ))}
    </ol>
  );
}
```

- [ ] **Step 2: Exit confirmation modal**

```tsx
// web/src/components/session/exit-confirmation.tsx
"use client";
import { useRouter } from "next/navigation";

export function ExitConfirmation({ open, onClose, hasProgress }: { open: boolean; onClose: () => void; hasProgress: boolean }) {
  const router = useRouter();
  if (!open) return null;
  const leave = () => router.push("/dashboard");
  if (!hasProgress) { leave(); return null; }
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold">Leave session?</h2>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">Your progress has been saved — you can pick up where you left off from your dashboard.</p>
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md px-4 py-2 text-sm">Continue</button>
          <button onClick={leave} className="rounded-md bg-[var(--blue)] px-4 py-2 text-sm text-white">Leave session</button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Modify session page to render full-screen with segment progress + close button**

In `web/src/app/(app)/session/[id]/page.tsx`, wrap the existing session UI:
- Top bar with just a close (X) button (right) and `<SegmentProgress />` (left, hidden if `segment_plan.length === 0`)
- On X click → open `<ExitConfirmation hasProgress={currentSegmentIdx > 0 || hasAnsweredAtLeastOne} />`
- The shell `(app)/layout.tsx` already hides its chrome on `/session/*` per Task 22

Concretely:
```tsx
"use client";
// existing imports plus:
import { useState } from "react";
import { ExitConfirmation } from "@/components/session/exit-confirmation";
import { SegmentProgress } from "@/components/session/segment-progress";

export default function SessionPage({ params }) {
  // existing state...
  const [showExit, setShowExit] = useState(false);
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b px-4 py-2">
        {session?.segment_plan?.length > 0 && (
          <SegmentProgress plan={session.segment_plan} currentIdx={session.current_segment_idx} />
        )}
        <button onClick={() => setShowExit(true)} aria-label="Close session"
          className="ml-auto p-2">✕</button>
      </header>
      <main className="flex-1 overflow-y-auto">
        {/* existing session UI: chat + cards */}
      </main>
      <ExitConfirmation open={showExit} onClose={() => setShowExit(false)}
        hasProgress={(session?.current_segment_idx ?? 0) > 0 || hasAnsweredAtLeastOne} />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add web/src/app/(app)/session/[id]/page.tsx web/src/components/session/
git commit -m "Make session full-screen with segment progress and smart exit confirmation"
```

---

## Phase J — Account Frontend (2 tasks)

### Task 30: Account page — Academic + Learning Preferences sections

**Files:**
- Create: `web/src/app/(app)/account/page.tsx`
- Create: `web/src/components/account/subject-card.tsx`
- Create: `web/src/components/account/edit-subject-modal.tsx`
- Create: `web/src/components/account/preferences-section.tsx`

- [ ] **Step 1: Account page composition**

```tsx
// web/src/app/(app)/account/page.tsx
"use client";
import { useEffect, useState } from "react";
import { accountApi } from "@/lib/api/account";
import { useFeatureFlag } from "@/lib/feature-flags";
import { redirect } from "next/navigation";
import { SubjectCard } from "@/components/account/subject-card";
import { PreferencesSection } from "@/components/account/preferences-section";
import { BillingSection } from "@/components/account/billing-section";
import { ProfileSection } from "@/components/account/profile-section";
import { DangerZone } from "@/components/account/danger-zone";

export default function AccountPage() {
  const v2 = useFeatureFlag("account_v2", true);
  if (!v2) redirect("/dashboard");
  const [data, setData] = useState<any | null>(null);
  useEffect(() => { accountApi.get().then(setData); }, []);
  if (!data) return <p>Loading…</p>;
  return (
    <div className="space-y-10">
      <Section id="academic" title="Academic Setup">
        {data.subjects.map((s: any) => <SubjectCard key={s.id} subject={s} onUpdated={() => accountApi.get().then(setData)} />)}
        <button disabled className="mt-2 rounded-lg border border-dashed border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)]"
          title="Coming soon">+ Add subject (Coming soon)</button>
      </Section>
      <Section id="learning-preferences" title="Learning Preferences">
        <p className="mb-3 text-sm text-[var(--text-secondary)]">These preferences personalise how Stride explains concepts. They don't change what you learn.</p>
        <PreferencesSection initial={data.preferences} />
      </Section>
      <Section id="profile" title="Profile"><ProfileSection profile={data.profile} /></Section>
      <Section id="billing" title="Billing"><BillingSection billing={data.billing} /></Section>
      <Section id="danger-zone" title="Danger Zone"><DangerZone /></Section>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id}>
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}
```

- [ ] **Step 2: Subject card + edit modal**

```tsx
// web/src/components/account/subject-card.tsx
"use client";
import { useState } from "react";
import { EditSubjectModal } from "./edit-subject-modal";

const SPEC_CODE: Record<string, string> = { edexcel: "9MA0", cambridge: "9709" };

export function SubjectCard({ subject, onUpdated }: { subject: any; onUpdated: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="rounded-lg border border-[var(--border)] bg-white p-4">
      <h3 className="font-semibold">{subject.subject.replace(/_/g, " ")}</h3>
      <p className="text-sm text-[var(--text-secondary)]">
        {subject.exam_board[0].toUpperCase() + subject.exam_board.slice(1)} · {SPEC_CODE[subject.exam_board]}
      </p>
      <dl className="mt-3 grid grid-cols-2 gap-y-1 text-sm">
        <dt className="text-[var(--text-secondary)]">Target grade</dt><dd>{subject.target_grade}</dd>
        <dt className="text-[var(--text-secondary)]">Exam</dt><dd>{subject.exam_date ?? "Not set"}</dd>
        <dt className="text-[var(--text-secondary)]">Readiness</dt><dd>{Math.round(subject.readiness_pct)}%</dd>
      </dl>
      <button onClick={() => setOpen(true)} className="mt-3 text-sm text-[var(--blue)]">Edit</button>
      {open && <EditSubjectModal subject={subject} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); onUpdated(); }} />}
    </article>
  );
}
```

```tsx
// web/src/components/account/edit-subject-modal.tsx
"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";
import { GradePicker } from "@/components/onboarding/fields/grade-picker";
import { ExamDatePicker } from "@/components/onboarding/fields/exam-date-picker";

export function EditSubjectModal({ subject, onClose, onSaved }: { subject: any; onClose: () => void; onSaved: () => void }) {
  const [examDate, setExamDate] = useState(subject.exam_date ?? "");
  const [targetGrade, setTargetGrade] = useState(subject.target_grade);
  const save = async () => {
    await accountApi.patchSubject(subject.id, { exam_date: examDate || null, target_grade: targetGrade });
    onSaved();
  };
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5">
        <h3 className="mb-4 text-lg font-semibold">Edit {subject.subject.replace(/_/g, " ")}</h3>
        <label className="mb-2 block text-sm">Exam date</label>
        <ExamDatePicker value={examDate} onChange={setExamDate} />
        <label className="mb-2 mt-4 block text-sm">Target grade</label>
        <GradePicker value={targetGrade} onChange={setTargetGrade} />
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2 text-sm">Cancel</button>
          <button onClick={save} className="rounded-md bg-[var(--blue)] px-3 py-2 text-sm text-white">Save</button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Preferences section**

```tsx
// web/src/components/account/preferences-section.tsx
"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";

const PREFS = [
  { key: "worked_examples", label: "Worked examples" },
  { key: "visual", label: "Visual explanations" },
  { key: "step_by_step", label: "Step-by-step explanations" },
  { key: "practice", label: "Practice questions" },
];

export function PreferencesSection({ initial }: { initial: Record<string, boolean> }) {
  const [state, setState] = useState(initial);
  const toggle = async (key: string) => {
    const next = { ...state, [key]: !state[key] };
    setState(next);
    await accountApi.patchPreferences(next);
  };
  return (
    <div className="grid gap-2">
      {PREFS.map(p => (
        <label key={p.key} className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--border)] bg-white p-3">
          <input type="checkbox" checked={!!state[p.key]} onChange={() => toggle(p.key)} />
          <span>{p.label}</span>
        </label>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add web/src/app/(app)/account/page.tsx web/src/components/account/subject-card.tsx web/src/components/account/edit-subject-modal.tsx web/src/components/account/preferences-section.tsx
git commit -m "Add account page with Academic + Learning Preferences sections"
```

---

### Task 31: Account page — Profile + Billing + Danger Zone

**Files:**
- Create: `web/src/components/account/profile-section.tsx`
- Create: `web/src/components/account/billing-section.tsx`
- Create: `web/src/components/account/danger-zone.tsx`

- [ ] **Step 1: Profile section (name editable; email read-only)**

```tsx
// web/src/components/account/profile-section.tsx
"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";

export function ProfileSection({ profile }: { profile: { name: string; email: string } }) {
  const [name, setName] = useState(profile.name);
  return (
    <div className="space-y-3">
      <label className="block text-sm">Name
        <input value={name} onChange={e => setName(e.target.value)}
          onBlur={() => accountApi.patchProfile({ name })}
          className="mt-1 w-full rounded-md border border-[var(--border)] px-3 py-2" />
      </label>
      <p className="text-sm text-[var(--text-secondary)]">Email: {profile.email}
        <button onClick={() => alert("Contact support to change your email")}
          className="ml-2 text-[var(--blue)]">Change</button>
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Billing section with benefits comparison**

```tsx
// web/src/components/account/billing-section.tsx
"use client";
import { apiFetch } from "@/lib/api";

export function BillingSection({ billing }: { billing: { tier: string; status: string } }) {
  const upgrade = async () => {
    const { url } = await apiFetch<{ url: string }>("/billing/checkout", { method: "POST" });
    window.location.href = url;
  };
  const portal = async () => {
    const { url } = await apiFetch<{ url: string }>("/billing/portal", { method: "POST" });
    window.location.href = url;
  };
  return (
    <div className="rounded-lg border border-[var(--border)] bg-white p-4">
      <p className="mb-3">Current Plan: <span className="font-semibold">{billing.tier === "free" ? "Free" : "Pro"}</span></p>
      {billing.tier === "free" ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Benefits title="Includes" items={["AI coaching", "Practice questions", "Diagnostic"]} />
            <Benefits title="Unlock with Pro" items={["Unlimited marking", "Past papers", "Advanced analytics"]} />
          </div>
          <button onClick={upgrade}
            className="mt-4 rounded-lg bg-[var(--blue)] px-4 py-2 text-white">Upgrade to Pro</button>
        </>
      ) : (
        <button onClick={portal}
          className="rounded-lg border border-[var(--border)] px-4 py-2">Manage subscription</button>
      )}
    </div>
  );
}

function Benefits({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-semibold">{title}</h4>
      <ul className="space-y-1 text-sm">{items.map(i => <li key={i}>✓ {i}</li>)}</ul>
    </div>
  );
}
```

- [ ] **Step 3: Danger zone**

```tsx
// web/src/components/account/danger-zone.tsx
"use client";
import { signOut } from "@/lib/auth";
import { useRouter } from "next/navigation";

export function DangerZone() {
  const router = useRouter();
  return (
    <div className="space-y-2 rounded-lg border border-red-200 bg-red-50 p-4">
      <button onClick={async () => { await signOut(); router.push("/login"); }}
        className="rounded-md bg-[var(--blue)] px-4 py-2 text-white">Sign out</button>
      <button onClick={() => alert("Contact support to delete your account")}
        className="block text-sm text-red-600">Delete account</button>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add web/src/components/account/profile-section.tsx web/src/components/account/billing-section.tsx web/src/components/account/danger-zone.tsx
git commit -m "Add account Profile, Billing, and Danger Zone sections"
```

---

## Phase K — Admin + Observability (2 tasks)

### Task 32: Admin student inspect page

**Files:**
- Create: `web/src/app/(admin)/admin/students/[id]/page.tsx`
- Create: `web/src/app/(admin)/layout.tsx`

- [ ] **Step 1: Layout (gates on `is_admin`)**

```tsx
// web/src/app/(admin)/layout.tsx
"use client";
import { redirect } from "next/navigation";
import { useStudent } from "@/lib/auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const student = useStudent();
  if (student && !student.is_admin) redirect("/dashboard");
  return <div className="mx-auto max-w-5xl px-4 py-6">{children}</div>;
}
```

- [ ] **Step 2: Inspect page (collapsible JSON renderer)**

```tsx
// web/src/app/(admin)/admin/students/[id]/page.tsx
"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export default function InspectPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<any | null>(null);
  useEffect(() => {
    apiFetch(`/admin/students/${params.id}/inspect`).then(setData);
  }, [params.id]);
  if (!data) return <p>Loading…</p>;
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Inspect: {data.profile.name}</h1>
      {Object.entries(data).map(([k, v]) => (
        <details key={k} className="rounded-lg border border-[var(--border)] bg-white p-3">
          <summary className="cursor-pointer font-semibold">{k}</summary>
          <pre className="mt-2 overflow-x-auto text-xs">{JSON.stringify(v, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/app/\(admin\)/
git commit -m "Add admin student-inspect page (read-only JSON, gated by is_admin)"
```

---

### Task 33: PostHog event wiring (8 new events)

**Files:**
- Modify: `web/src/app/(onboarding)/onboarding/*/page.tsx` (capture `onboarding_step_completed` per step submit)
- Modify: `web/src/app/(onboarding)/onboarding/roadmap/page.tsx` (capture `onboarding_completed` on finalize)
- Modify: `app/services/today_focus_service.py` (capture `today_focus_generated`)
- Modify: `app/agents/orchestrator.py` (capture `segment_started` / `segment_completed`)
- Modify: `app/services/readiness_service.py` (capture `readiness_changed` when delta > 0)
- Modify: `web/src/components/shell/notification-bell.tsx` (capture `notification_clicked` on item click)
- Modify: `app/api/v1/endpoints/onboarding.py` (capture `diagnostic_completed` after diagnostic session ends — wire as a notification emit + posthog event)

**Helper:** existing `app/core/telemetry.py` exposes `posthog.capture(distinct_id, event, properties)`. Use that. Frontend uses `posthog.capture(event, props)` from `posthog-js`.

- [ ] **Step 1: Backend events — wire one site at a time**

In `app/services/today_focus_service.py` `get_or_generate`, after persisting:
```python
from app.core.telemetry import posthog
posthog.capture(str(student_id), "today_focus_generated", {
    "shape": shape, "intents": [s["intent"] for s in plan],
    "topics": [s["topic"] for s in plan], "generator_version": GENERATOR_VERSION,
})
```

In `app/agents/orchestrator.py` `step_session`, before invoking handler and after segment completes:
```python
posthog.capture(state["student_id"], "segment_started", {
    "intent": seg["intent"], "handler": seg["handler"],
    "topic": seg.get("topic"), "target_minutes": seg["target_minutes"], "segment_idx": idx,
})
# ... after handler.step returns and segment_complete is true:
posthog.capture(state["student_id"], "segment_completed", {
    "intent": seg["intent"], "handler": seg["handler"],
    "topic": seg.get("topic"), "target_minutes": seg["target_minutes"],
    "segment_idx": idx, "outcome": "completed",
})
```

In `app/services/readiness_service.py` `write_snapshot_if_first_today`, after writing the new snapshot:
```python
# Find previous snapshot and emit readiness_changed if delta exists
prev = (await db.execute(
    select(ReadinessSnapshot).where(
        ReadinessSnapshot.student_id == student_id,
        ReadinessSnapshot.subject == subject,
        ReadinessSnapshot.snapshot_date < today,
    ).order_by(ReadinessSnapshot.snapshot_date.desc()).limit(1)
)).scalar_one_or_none()
if prev and abs(snap.readiness_pct - prev.readiness_pct) > 0.1:
    from app.core.telemetry import posthog
    posthog.capture(str(student_id), "readiness_changed", {
        "subject": subject, "prev_pct": prev.readiness_pct,
        "new_pct": snap.readiness_pct, "delta": snap.readiness_pct - prev.readiness_pct,
    })
    if snap.readiness_pct - prev.readiness_pct >= 1.0:
        from app.services.notification_service import emit
        await emit(db, student_id, "readiness_increased",
                   payload={"subject": subject, "delta": round(snap.readiness_pct - prev.readiness_pct, 1)})
```

- [ ] **Step 2: Frontend events**

In each onboarding step page, after successful POST:
```typescript
import posthog from "posthog-js";
posthog.capture("onboarding_step_completed", { step_name: "subjects", time_on_step_sec: 12 });
```

In roadmap page finalize handler:
```typescript
posthog.capture("onboarding_completed", {
  took_diagnostic: /* known from session history */,
  subjects: [...], board: "edexcel", time_to_complete_sec: 0,
});
```

In notification-bell on item click:
```typescript
posthog.capture("notification_clicked", { type: n.type });
```

- [ ] **Step 3: Commit**

```bash
git add app/services/today_focus_service.py app/services/readiness_service.py \
        app/agents/orchestrator.py web/src/app/(onboarding)/ \
        web/src/components/shell/notification-bell.tsx
git commit -m "Wire PostHog analytics events: 8 new event types across backend + frontend"
```

---

## Phase L — Rollout (1 task)

### Task 34: Smoke test script + deploy checklist + flag setup

**Files:**
- Create: `tests/smoke/onboarding_to_session.py`
- Create: `docs/superpowers/deploys/2026-06-28-ux-overhaul-deploy.md`

**Not committed to code:** the actual flag creation in PostHog dashboard — done manually with each flag set to 100% rollout, all known flags created.

- [ ] **Step 1: Smoke test script**

```python
# tests/smoke/onboarding_to_session.py
"""Post-deploy smoke test — runs against production-shaped API."""
import os, sys, json
import requests

BASE = os.environ.get("STRIDE_API_BASE", "http://localhost:8000")


def main():
    # Register a throwaway test user
    email = f"smoke+{os.getpid()}@test.stride"
    r = requests.post(f"{BASE}/api/v1/auth/register",
                      json={"email": email, "name": "Smoke", "password": "ThrowAway123!"})
    r.raise_for_status()
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}

    # Walk onboarding
    requests.post(f"{BASE}/api/v1/onboarding/education-system", json={"system": "a_level"}, headers=h).raise_for_status()
    requests.post(f"{BASE}/api/v1/onboarding/subjects", json={"subjects": ["pure_mathematics"]}, headers=h).raise_for_status()
    requests.post(f"{BASE}/api/v1/onboarding/exam-board", json={"subject_boards": {"pure_mathematics": "edexcel"}}, headers=h).raise_for_status()
    requests.post(f"{BASE}/api/v1/onboarding/exam-date", json={"subject_dates": {"pure_mathematics": "2027-06-01"}}, headers=h).raise_for_status()
    requests.post(f"{BASE}/api/v1/onboarding/target-grade", json={"subject_grades": {"pure_mathematics": {"target": "A*"}}}, headers=h).raise_for_status()
    requests.post(f"{BASE}/api/v1/onboarding/preferences", json={"worked_examples": True, "visual": False, "step_by_step": True, "practice": False}, headers=h).raise_for_status()
    fin = requests.post(f"{BASE}/api/v1/onboarding/finalize", headers=h)
    fin.raise_for_status()
    assert fin.json()["redirect_to"] == "/dashboard"

    # Dashboard renders
    r = requests.get(f"{BASE}/api/v1/dashboard/pure_mathematics", headers=h)
    r.raise_for_status()
    body = r.json()
    assert "today_focus" in body
    assert body["target_grade"] == "A*"
    assert len(body["today_focus"]["segment_plan"]) == 3

    # /readyz
    r = requests.get(f"{BASE}/readyz")
    r.raise_for_status()
    assert r.json()["status"] == "ready"

    print("SMOKE OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SMOKE FAIL: {e}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 2: Deploy checklist document**

```markdown
# UX Overhaul Sub-project #1 — Deploy Checklist
Date: 2026-06-28

## Pre-deploy
- [ ] All Phase A–K tasks merged
- [ ] PostHog flags created (all defaulting to 100%): dashboard_v2, onboarding_v2,
      session_engine_v2, notifications_v2, account_v2
- [ ] Sentry alert noise threshold raised 2× for 48h (set in Sentry project settings)

## Backend deploy (Cloud Run)
1. From repo root: `gcloud builds submit --tag europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:ux1 --region europe-west2 .`
2. `gcloud run deploy ascend-api --image europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:ux1 --region europe-west2 --platform managed --min-instances 1`
3. Migration runs at container startup; watch logs: `gcloud run logs read ascend-api --region europe-west2`
4. Confirm `/readyz` returns 200:
   `curl https://ascend-api-770225551335.europe-west2.run.app/readyz`

## Seed verification
- [ ] `psql $SUPABASE_URL -c "SELECT exam_board, count(*) FROM syllabus_topics WHERE version='2026.1' GROUP BY exam_board;"`
      Expected: edexcel=22, cambridge=17
- [ ] `psql $SUPABASE_URL -c "SELECT count(*) FROM learner_subjects;"`
      Expected: ≥ count of pre-existing onboarded students
- [ ] Smoke test: `STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app python tests/smoke/onboarding_to_session.py`

## Frontend deploy (Vercel)
1. Push the merge commit to `main` — Vercel auto-deploys.
2. Wait for green Vercel deployment.
3. Visit https://tutor-agent-nu.vercel.app — confirm new shell + dashboard render.

## Post-deploy
- [ ] Click through onboarding as a new test user
- [ ] Run dashboard / account / session smoke manually
- [ ] Watch Sentry for 1 hour; investigate any new error patterns
- [ ] Watch PostHog live events: confirm `onboarding_completed`, `today_focus_generated`,
      `segment_started` are firing

## Rollback levers (in order)
1. PostHog flag off per surface (no deploy needed, <30s)
2. Cloud Run revision pin: `gcloud run services update-traffic ascend-api --to-revisions=<previous>=100 --region europe-west2`
3. Vercel instant rollback in dashboard

## Notes
- Migration is additive — code rollback is safe.
- Legacy components are still in `web/src/app/(app)/dashboard/_legacy.tsx` etc.
- Cleanup PR deletes legacy code after 2–4 weeks of stable production.
```

- [ ] **Step 3: Commit**

```bash
git add tests/smoke/onboarding_to_session.py docs/superpowers/deploys/
git commit -m "Add smoke test script and deploy checklist for UX overhaul sub-project #1"
```

---

## Self-Review

Spec coverage check completed inline during writing. Key items mapped:

| Spec section | Implementing tasks |
|---|---|
| §4 Data model | Tasks 1, 2 |
| §5 Onboarding flow | Tasks 16, 23, 24, 25 |
| §6 Dashboard surface | Tasks 13, 14, 15, 26, 27, 28 |
| §7 Session engine | Tasks 8, 9, 10, 11, 12, 29 |
| §8 Account page + shell | Tasks 17, 22, 30, 31 |
| §9 Feature flags | Tasks 7, 20 |
| §10 Observability | Task 33 |
| §11 Health checks | Task 18 (/readyz) |
| §12 Versioning | Tasks 1 (syllabus_version, session_version columns), 14 (generator_version on history) |
| §13 Admin tooling | Tasks 19, 32 |
| §14 Testing | Tasks 3, plus per-task tests throughout |
| §15 Rollout | Task 34 |

**Acknowledged open questions** (spec §17, deferred to plan-time decisions surfacing during implementation):
- Exact syllabus topic lists for Edexcel 9MA0 vs Cambridge 9709 — shipped in Task 2 as a best-effort list per author; verify against current `study_plan_service` content before merging Task 2.
- Soft-delete account flow existence — Task 31's danger zone falls back to `alert("Contact support")`. If a server-side soft-delete exists, wire it in Task 31's button.
- Stripe `subscription_renewed` webhook — verify existing webhook handler emits a notification via `notification_service.emit` (small modification to `app/api/v1/endpoints/billing.py` webhook handler — fold into Task 33 if not already done).
- Mobile breakpoints for full-screen Account edit modals — handled via Tailwind `sm:`/`md:` utilities; manual QA on iPhone-size viewport during Task 30.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-stride-ux-overhaul-shell-onboarding-dashboard.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
