# Stride UX Overhaul — Sub-project #1: Onboarding + Dashboard + Shell

**Status:** Design approved, awaiting implementation plan
**Date:** 2026-06-28
**Author:** Min Thant Tin (with Claude)
**Scope:** Sub-project #1 of 5 in the wider Stride UX overhaul

---

## 1. Context

Stride is currently a chat-first AI tutor: students land in a free-flowing 5-phase Socratic session. The new product vision recasts Stride as an **AI exam coach**: students see a focused dashboard with countdown, readiness, and a structured "Today's Focus" plan. Chat becomes a tool inside the session, not the product surface itself.

The full vision spans 5 independent subsystems. Trying to design them in one spec produces a vague mega-design. This spec covers **only sub-project #1**: the new onboarding, dashboard, shell, account page, and the session-engine changes those surfaces depend on. Other sub-projects (#2 Practice modes, #3 Exam Marker, #4 Flashcards, #5 Engagement loop) get their own spec/plan/implement cycles in build order — sub-project #1 lands first because every other surface lives inside its shell.

**Subjects supported at launch (unchanged from current product):** Pure Mathematics × Edexcel (9MA0) and Pure Mathematics × Cambridge (9709). The onboarding UI exposes more subjects/boards/systems but marks unsupported ones "Coming soon".

## 2. Goals & non-goals

### Goals
1. Replace chat-first UX with dashboard-first coaching surface
2. Multi-step onboarding that produces a learner profile, optional diagnostic seed, and a personalized first dashboard
3. Dashboard that answers "what should I do today?" with a 3-segment Today's Focus session
4. Structured session engine supporting per-segment intent + handler
5. Account page that mirrors onboarding fields for ongoing edits
6. In-app notification center
7. Minimal admin tooling for debugging "my roadmap looks wrong"
8. Single deploy with kill-switch feature flags per surface

### Non-goals (deliberate, owned by later sub-projects)
- Push/email notifications (sub-project #5 Engagement)
- Per-topic drill-in pages, Practice mode picker (sub-project #2 Practice)
- Image/PDF upload, exam marking pipeline (sub-project #3 Exam Marker)
- Flashcards + spaced repetition (sub-project #4 Flashcards)
- Real grade-prediction model (later, when training data exists)
- Waitlist capture for unsupported subjects/boards
- Admin event timeline + action buttons (admin tooling sub-project)
- Syllabus version opt-in flow for existing students

## 3. Approach

**Approach A — Replace in place, with feature-flag kill-switches.**

Rewrite the existing `(app)/dashboard` and `(onboarding)/onboarding` route groups in `web/`. Delete the standalone `/progress` route — its data folds into the new dashboard. Add `/account`. Extend the existing tutor engine to support segment plans + diagnostic sessions. New shell ships as the default for all users (no parallel route group), but each surface is wrapped in a PostHog feature flag check that lets us flip back to the legacy component without a code rollback. Old code paths stay in the codebase for one release (2–4 weeks) and get deleted in a follow-up cleanup PR after production stability is confirmed.

Single deploy. Migration is additive (no DROPs in this sub-project). Rollback levers are: (1) flip flag off per surface, (2) code rollback via Cloud Run revision pin + Vercel instant rollback.

Alternatives considered: a parallel `(v2)` route group behind cohort flags (overkill for current beta-stage user count), and a shell-only rewrite that left the session engine unchanged (visible promise/delivery gap with the dashboard's structured-coaching framing).

## 4. Data model

All new tables and columns. No DROPs in this sub-project; old `Student.exam_board / subjects / exam_date` columns stay one release as fallback then drop in a cleanup migration.

### New tables

**`learner_subjects`** — per-subject profile, replacing the flat fields on `Student`:
```
id uuid PK
student_id uuid FK -> students(id)
subject text                  -- "pure_mathematics"
exam_board text               -- "edexcel" | "cambridge"
exam_level text               -- "a_level" | "gcse" | "ib" | "university"
exam_date date NULL           -- nullable: "don't know yet"
target_grade text             -- "A*" | "A" | "B" | "C" | "D" | "E"
current_grade text NULL       -- optional self-report
syllabus_version text         -- e.g. "2026.1", pinned at onboarding
recommended_minutes_per_day int NULL  -- computed at onboarding; recomputed on exam_date / target_grade change
is_draft boolean default true -- onboarding-in-progress marker
created_at, updated_at timestamptz
UNIQUE (student_id, subject)
```

**`syllabus_topics`** — seed table; source of truth for readiness % calculation:
```
id uuid PK
exam_board text
subject text
version text                  -- "2026.1"
topic_id text                 -- stable string id, e.g. "pure_maths.integration"
topic_name text               -- human-readable
parent_topic_id text NULL     -- for hierarchy
ordinal int                   -- syllabus order
UNIQUE (exam_board, subject, version, topic_id)
```
Seeded in migration for Edexcel 9MA0 Pure Maths and Cambridge 9709 Pure Maths (version `2026.1`).

**`readiness_snapshots`** — lazily-written daily snapshots, supports "+X% this month" trend:
```
id uuid PK
student_id uuid FK
subject text
snapshot_date date
readiness_pct numeric
created_at timestamptz
UNIQUE (student_id, subject, snapshot_date)
```
Written on first dashboard load per day (no cron). Trend line gates on ≥7 days of history.

**`notifications`** — in-app notification center:
```
id uuid PK
student_id uuid FK
type text                     -- "readiness_increased", "diagnostic_complete", etc.
payload jsonb                 -- type-specific data
read_at timestamptz NULL
created_at timestamptz default now()
INDEX (student_id, read_at, created_at DESC)
```
Written by event handlers in `session_service`, `study_plan_service`, `billing_service` via a new `emit_notification(...)` helper. No background workers in this sub-project.

**`today_focus_history`** — persisted Today's Focus records for analysis:
```
id uuid PK
student_id uuid FK
subject text
focus_date date
generator_version text        -- "1.0" at launch
shape text                    -- "onboarding" | "build" | "default" | "exam_ready"
segment_plan jsonb            -- full plan with intent/handler/why per segment
reasoning jsonb               -- [{segment_idx, factors: {...}}]
generated_at timestamptz
expires_at timestamptz
UNIQUE (student_id, subject, focus_date)
```
Redis stays as the read-cache; this table is for longitudinal analytics ("did generator v2 convert better than v1?").

### Changes to existing tables

**`students`** — new columns:
- `preferences jsonb default '{}'` — `{worked_examples: bool, visual: bool, step_by_step: bool, practice: bool}`
- `onboarded_at timestamptz NULL` — set when onboarding wizard completes (existing `onboarding_complete` bool stays)
- `is_admin boolean default false` — gates admin tooling

**`sessions` (TutorSession)** — new columns:
- `session_type text default 'practice'` — `'diagnostic' | 'practice'`
- `session_version int default 2` — `1` = legacy single-phase, `2` = segment-based
- `segment_plan jsonb default '[]'` — see segment shape below
- `current_segment_idx int default 0`

### Segment shape (inside `segment_plan` JSON)

```json
{
  "idx": 0,
  "intent": "revise",
  "handler": "review",
  "topic": "integration",
  "why": "Because you've lost marks on substitution questions recently.",
  "target_minutes": 10,
  "status": "pending",
  "config": {}
}
```

- `intent` enum: `diagnose | teach | reinforce | assess | revise | consolidate` — stable, used by planning + analytics
- `handler` enum: `diagnostic_question | practice | review | mistakes` — implementation; can be swapped
- `status`: `pending | in_progress | done | error`

### Migration

Single Alembic revision that:
1. Creates the 5 new tables
2. Seeds `syllabus_topics` for Edexcel 9MA0 + Cambridge 9709 Pure Maths (version `2026.1`)
3. Backfills `learner_subjects` from each existing `Student.subjects` × `exam_board` × `exam_date` (drops `is_draft=true` flag on backfilled rows — they're not drafts)
4. Adds new `students` columns with defaults
5. Adds new `sessions` columns; sets `session_version=1` on all existing rows (so legacy resume path triggers)
6. Records the active syllabus version (`2026.1`) on every backfilled `learner_subjects` row

Old `Student.exam_board / subjects / exam_date` columns retained.

## 5. Onboarding flow

Linear wizard, one route per step under `/onboarding/*`. Server-driven step routing (an `/onboarding/state` endpoint returns `next_step` + current draft) — the client doesn't encode step order, so inserting/removing steps is a backend-only change.

Drafts persisted server-side on every step submit. Tab close → resume on the furthest-completed step.

| # | Route | Purpose |
|---|---|---|
| 1 | `/onboarding/welcome` | Single CTA: "Meet Alex, your AI exam coach. Let's set up your study plan." → `[Get Started]` |
| 2 | `/onboarding/education-system` | A Levels / GCSE / IB / University. Only A Levels enabled; others disabled with "Coming soon" tooltip |
| 3 | `/onboarding/subjects` | Multi-select grid. Pure Maths enabled; Physics / Chemistry / Mechanics & Statistics disabled |
| 4 | `/onboarding/exam-board` | Per selected subject: Edexcel + Cambridge enabled; AQA / OCR disabled |
| 5 | `/onboarding/exam-date` | Date picker per subject. "Don't know yet" option allowed (sets default 6mo out; dashboard labels as estimated) |
| 6 | `/onboarding/target-grade` | Current grade (optional) + target grade per subject (A*/A/B/C/D/E) |
| 7 | `/onboarding/assessment` | Two cards: `[Take 10-min diagnostic — recommended]` / `[Skip for now]` |
| 8 | `/onboarding/preferences` | Four checkboxes: worked examples / visual / step-by-step / practice. Writes to `Student.preferences` |
| 9 | `/onboarding/roadmap` | First dashboard preview: subject, days until exam, initial readiness %, recommended study mins/day, top 3 priority topics, `[Start your first session]` → dashboard. On click: all draft `learner_subjects` rows flipped to `is_draft=false`, `Student.onboarded_at = now()`, `Student.onboarding_complete = true`, then redirect to `/dashboard` |

**Diagnostic (Step 7):** launches a `session_type=diagnostic` session with 7 segments, one per major Pure Maths topic area (seeded per board: Algebra, Trigonometry, Differentiation, Integration, Sequences & Series, Functions, Vectors). Each segment uses `handler=diagnostic_question`: single calibration question, no hints, no second chance. After all 7 complete, each evaluated answer writes a `MasteryState` row with `mastery_score = correct ? 0.6 : 0.2` (mid-band — one question is weak signal). Onboarding wizard resumes after diagnostic session ends.

**Skip path:** writes no mastery rows; dashboard cold state copy adjusts.

**Gating unsupported combos:** UI shows everything but disables unsupported options visually with "Coming soon" tag. Backend defensively rejects unsupported combos on each step submit. No waitlist capture in this sub-project.

**Recommended study mins/day:** computed at end of onboarding (and whenever a subject is added later via Account) from `(syllabus_topics_remaining × ~15min/topic) / days_until_exam`, clamped to `[20, 90]`. Displayed on roadmap and dashboard. Stored on `learner_subjects` so it doesn't recompute on every dashboard load; recomputed when exam date or target grade changes.

**Component reuse:** subject/board/date/grade form pieces live at `web/src/components/onboarding/fields/*`, imported by both wizard and account modal.

## 6. Dashboard surface

Route: `/dashboard`. Single subject view; subject switcher in header (hidden when only one subject exists). Sections top-to-bottom:

### 1. Header strip
`Good morning, {name}.` + subject switcher (`Pure Maths ▾`) when ≥2 subjects exist.

### 2. Exam countdown + goal band
Three stacked items:
- `Pure Maths exam — 18 days remaining` (from `learner_subjects.exam_date`)
- `Target grade: A*`
- `Current prediction: B` — heuristic bucketing from readiness %: `≥90→A*, ≥75→A, ≥60→B, ≥45→C, ≥30→D, else E`. Copy hedges with "estimated". Hidden until ≥7 days of history.

Edge cases:
- `exam_date` in past → `Exam has passed — set a new date in Account →`
- `exam_date > 365d out` → `1 year+ until exam` (avoids ugly "428 days")
- `exam_date IS NULL` → `Estimated: ~6 months` + `[Set exam date]` link

### 3. Readiness card
Large `%`, progress bar.
- With ≥7 days history: `+14% this month` (vs nearest snapshot ≥28d back)
- Cold state: `You're just getting started — complete a few study sessions and we'll begin tracking your improvement over time.`

Calculation: `count(MasteryState WHERE mastery_score ≥ 0.7 AND topic IN syllabus_topics) / count(syllabus_topics for student's board+subject+pinned_version)`.

### 4. Resume Session card (conditional)
When a `TutorSession` exists with `ended_at IS NULL` AND `current_segment_idx < len(segment_plan)`:
```
Resume today's session
Completed: 1 / 3 segments
[Continue]
```
Renders *above* Today's Focus and replaces its `[Start Session]` CTA until resolved (completed or auto-closed at 24h).

Stale resume cleanup: any session with `ended_at IS NULL` AND `started_at < now() - 24h` is auto-marked `ended_at = started_at + 24h` by a cleanup query on dashboard load (no cron).

### 5. Today's Focus card
Header: `Today's Session · 35 min` + `Complete these three activities to stay on track for your target grade.`

Progress dots row at top: `○ Review · ○ Practice · ○ Reflect` → fills `●` while in-progress, `✓` when complete; persists across tab close.

3 numbered items, each with title · duration · `Why:` line:
```
1. Review Integration · 10 min
   Because you've lost marks on substitution questions recently.

2. Practice Differentiation · 15 min
   Recommended because your mastery dropped below 60%.

3. Review Recent Mistakes · 5 min
   Three questions from yesterday's session — let's lock them in.
```

Single `[Start Session]` CTA. After completion: `Done for today — great work` + `[Optional bonus session]`.

### 6. Recent activity line
Single short row below Today's Focus:
- Hot: `Last studied: yesterday · Integration Practice · scored 78%`
- Cold (≥3d gap): `You haven't studied for 5 days. Let's get back on track.`
- Brand new (zero sessions): hide entirely

### 7. Strong / Weak topics
Top 3 each from `MasteryState` ordered by score. Read-only in this sub-project (per-topic drill-in is owned by Practice sub-project).

---

### Today's Focus generation (`today_focus_service`)

Picks a *shape* from student state, then fills slots with intent / handler / config / why.

| Shape | When chosen | Slots (intent / handler / config) |
|---|---|---|
| `onboarding` | `sessions_count < 3` | `teach / practice / learn`, `teach / practice / walkthrough`, `assess / practice / mini_quiz` |
| `build` | readiness < 40% OR avg mastery trending down 7d | `teach / practice / learn`, `reinforce / practice / —`, `revise / review / —` |
| `default` | steady mid-journey state | `revise / review / —`, `reinforce / practice / —`, `consolidate / mistakes / —` |
| `exam_ready` | `days_until_exam ≤ 14` AND readiness ≥ 75% | `assess / practice / timed_exam`, `consolidate / mistakes / —`, `revise / mistakes / flash` |

Slot generators pick the concrete topic and produce the `why` string from intent-keyed templates:
- `diagnose` → `Let's see where you are with {topic}.`
- `teach` → `This topic is new for you — let's build it up.`
- `reinforce` → `Your mastery on {topic} dropped to {pct}%. Let's bring it back up.`
- `assess` → `Time to test what you've learned — no hints this round.`
- `revise` → `Three questions from {date}'s session — let's lock them in.`
- `consolidate` → `Reviewing concepts you've nearly mastered to make them stick.`

Why-string templating is deterministic (not LLM-generated) for speed + reproducibility.

**Caching:** Redis key `today_focus:{student_id}:{subject}:{yyyy-mm-dd}`, TTL until midnight student-local. Persisted to `today_focus_history` table on generation. Idempotent via Redis `SETNX` (handles dual-device race).

**Failure fallback:** if generation throws, return a single-segment plan `[{intent: reinforce, handler: practice, topic: weakest_topic}]` and log to Sentry.

## 7. Session engine changes

Outer structure: segments replace phases. Existing 5-phase logic effectively becomes the `practice` handler with intro/consolidation framing applied per-session-bookend, not per-segment.

### Handlers shipped in this sub-project

| Handler | Behavior | Used by |
|---|---|---|
| `diagnostic_question` | Single calibration question, no hints, no second chance. Records mastery seed | `diagnostic` session type |
| `practice` | Question → eval (hints allowed). 1–3 questions per segment based on time/perf | All shapes' `practice` slot; backs `learn`/`walkthrough`/`timed_exam`/`mini_quiz`/`flash_review` via config |
| `review` | Revisits a recent miss; asks same concept in different framing; eval | `default`/`build`/`exam_ready` shapes |
| `mistakes` | Pulls 1–3 below-threshold answers from recent sessions; walks corrections | `default`/`exam_ready` shapes |

### Configuration variants (no new handlers needed)

- `learn` = `practice` + system-prompt addendum: "Open with a worked example before asking the student to attempt."
- `walkthrough` = `practice` + `auto_answer=true` (tutor solves, student watches; no scored eval)
- `mini_quiz` = three back-to-back `practice` micro-rounds with `allow_hints=false`, summary at end
- `timed_exam` = `practice` + `time_limit_seconds` (frontend enforces countdown; backend records elapsed)
- `flash_review` = `mistakes` + `pace=rapid`

All 4 dashboard shapes function with these 4 handlers + config flags.

### Segment transitions

When a segment's terminating condition fires (max questions, target_minutes elapsed, or explicit `complete` from handler):
1. Marks `segment.status = done`
2. Updates mastery deltas from segment's evaluations
3. If `idx+1 < len(plan)`: emits transition message `Nice work — let's move on to your {next.title}.`, advances `current_segment_idx`, invokes next handler
4. If last segment: emits reflection card (`Great session — your Integration mastery went from 65% to 71%. Tomorrow: continue with differentiation.`), marks session complete (`ended_at = now()`), invalidates Today's Focus Redis cache so tomorrow's regenerates

### Resume

`SessionState` in `app/workflows/state.py` gains `current_segment_idx` + per-segment `progress_state`. On reconnect, orchestrator restores from Redis (or rebuilds from Postgres if Redis evicted), re-renders the in-progress segment's last turn, and continues.

### Preference injection

At session start, `build_system_prompt()` adds a `<student_preferences>` block from `Student.preferences`:
- `worked_examples=true` → `"This student learns best from worked examples. When introducing a concept, show a complete worked example before asking them to attempt their own."`
- `step_by_step=true` → `"This student prefers granular step-by-step explanations. Break hints into the smallest meaningful steps."`
- `visual=true` → `"This student finds diagrams helpful. Where a diagram would clarify (graphs, geometric setups, free-body diagrams), describe one in ASCII or LaTeX even if not explicitly asked."`
- `practice=true` → `"This student learns by doing. Keep explanations short; prioritise getting them to a question quickly."`

Empty/unset → no addendum (default behavior).

### Diagnostic session specifics

`session_type=diagnostic`, `segment_plan` = 7 segments of `intent=diagnose, handler=diagnostic_question`, one per major topic area seeded per board. No hints. After all 7 complete, each evaluated answer writes a `MasteryState` row with `mastery_score = correct ? 0.6 : 0.2`. Onboarding wizard resumes after.

### Backwards compatibility

Migration sets `session_type=practice`, `session_version=1`, `segment_plan=[{idx:0, type:"practice", topic:row.topic, ...}]`, `current_segment_idx=0` on existing rows. Orchestrator transparently shims v1 sessions into single-segment v2 plans at load time.

### Error handling

- LLM 429/timeout → existing 3-model Groq fallback handles
- Single segment handler failure → caught at orchestrator; segment marked `error`, friendly "Hit a snag — let's try again" + `[Retry]` button. Other segments preserved
- Diagnostic LLM failure mid-onboarding → draft persisted, retry or Skip always available

## 8. Account page + shell

### Shell

- **All viewports:** top bar with logo (left, → `/dashboard`), notification bell (right), avatar menu (right) → `Account · Sign out`. No hamburger — only two destinations.
- **Session view:** full-screen takeover, shell chrome hidden. Single close button top-right with smart confirmation:
  - `progress == 0%` → exit immediately, no modal
  - `progress > 0%` → modal: `Leave session?` + `Your progress has been saved — you can pick up where you left off from your dashboard.` + `[Continue] [Leave session]`

### Routes after this sub-project

| Route | Status |
|---|---|
| `/dashboard` | Rewritten |
| `/onboarding/*` | Rewritten as multi-step wizard |
| `/session/[id]` | Kept; segment-aware; chrome hidden |
| `/account` | New |
| `/admin/students/[id]` | New (admin-only) |
| `/progress` | Deleted; old route returns 410 → redirect `/dashboard` |
| `/pricing` | Kept for logged-out marketing only; logged-in users redirect to `/account#billing` |
| `/login` `/register` `/forgot-password` `/reset-password` | Unchanged |

### Account page (`/account`)

Single page, anchored sections, academic-first ordering:

1. **`#academic`** — list of `learner_subjects`. Enriched card per subject:
   ```
   Pure Mathematics
   Cambridge · 9709

   Target Grade: A*       Exam: 15 Nov 2026
   Readiness: 72%

   [Edit]
   ```
   `[Add subject]` visible-but-disabled with tooltip `Coming soon` until ≥2 supported subjects exist.

2. **`#learning-preferences`** — renamed from "Preferences". Helper text: `These preferences personalize how Stride explains concepts. They don't change what you learn.` Four checkboxes; save-on-change with optimistic update; effects on next session start.

3. **`#profile`** — name (editable), email (read-only with `Contact support to change` toast).

4. **`#billing`** — tier badge + benefits comparison:
   - Free: `Includes: ✓ AI coaching ✓ Practice ✓ Diagnostic` + `Unlock with Pro: ✓ Unlimited marking ✓ Past papers ✓ Advanced analytics` + `[Upgrade to Pro]` → Stripe Checkout (existing `billing_service`)
   - Pro: hides unlock list; shows renewal date + `[Manage subscription]` → Customer Portal (existing flow)

5. **`#danger-zone`** — `[Sign out]` primary; `[Delete account]` secondary opens confirm dialog → soft-delete with 30-day grace. If server-side delete flow doesn't exist, fall back to `Contact support to delete your account` toast (implementer decides at plan time).

### Notification center

- Bell icon in top bar with unread-count badge. Click → dropdown panel listing latest 20 items.
- **Event types in this sub-project:**
  - `readiness_increased` — `Your readiness increased by 4%`
  - `diagnostic_complete` — `Your diagnostic is ready — view your roadmap`
  - `subscription_renewed` — `Your Pro subscription renewed`
  - `session_reminder` — in-app only at session end: `Tomorrow: continue with differentiation` (push delivery is sub-project #5)
- Marked read on click; `Mark all read` button at top.
- Empty state: `No notifications yet.`
- Failure: badge blank, dropdown shows `Couldn't load — retry`.

## 9. Feature flags

PostHog flags (already integrated). Used as kill-switches per surface — NOT for cohort A/B testing.

| Flag | Off-state behavior |
|---|---|
| `dashboard_v2` | Renders legacy dashboard component |
| `onboarding_v2` | Renders legacy onboarding wizard |
| `session_engine_v2` | Backend forces single-segment plan for new sessions |
| `notifications_v2` | Bell icon hidden, no notification writes |
| `account_v2` | `/account` returns 410 → redirect `/dashboard` |

**Defaults:** all `true` for everyone (beta-stage user count justifies immediate 100% rollout). Flags exist so a surface can be flipped off in <30s during incident response without code rollback.

**Old code retention:** legacy components kept in codebase for one release (2–4 weeks). Cleanup PR deletes them once production stability is confirmed.

## 10. Observability — product analytics events

Existing PostHog events stay: `session_started, session_resumed, session_ended, question_generated, question_submitted, answer_evaluated, signal_clicked, study_plan_generated, checkout_started`.

**Deprecated:** `phase_advanced` (phases replaced by segments).

**New events:**

| Event | Fires when | Properties |
|---|---|---|
| `onboarding_step_completed` | Each step submit | `step_name, time_on_step_sec` |
| `onboarding_completed` | Wizard finishes | `took_diagnostic, subjects, board, time_to_complete_sec` |
| `diagnostic_completed` | Diagnostic session ends | `topics_assessed, mastery_seed_avg` |
| `today_focus_generated` | `today_focus_service` writes new focus | `shape, intents[], topics[], generator_version` |
| `segment_started` | Segment handler invoked | `intent, handler, topic, target_minutes, segment_idx` |
| `segment_completed` | Segment terminates | `intent, handler, topic, target_minutes, actual_minutes, segment_idx, outcome` |
| `readiness_changed` | New snapshot has delta vs previous | `subject, prev_pct, new_pct, delta` |
| `notification_clicked` | Bell dropdown row click | `type` |

## 11. Health checks

- `/healthz` — existing liveness, unchanged.
- `/readyz` — **new readiness probe** for Cloud Run startup probe. Returns 503 if any of:
  - DB connection fails
  - Redis ping fails
  - `count(syllabus_topics WHERE version='2026.1') = 0` for any supported board
  - `GROQ_API_KEY` env var missing
  - Alembic head mismatch (DB schema not at HEAD)

Fail-fast prevents partial-functionality state.

## 12. Versioning

### Session versioning
`TutorSession.session_version int default 2`. Migration backfills existing rows to `1`. Orchestrator inspects version on load: v1 = legacy single-phase (transparent shim to single-segment v2 plan), v2 = native segment. Future v3 schema changes have a clear discriminator.

### Syllabus versioning
`syllabus_topics` keyed on `(exam_board, subject, version, topic_id)`. Initial seed `version=2026.1`. `learner_subjects.syllabus_version` pins per-student version at onboarding. Readiness % + Today's Focus always query the student's pinned version. A new syllabus version becomes default for new students; existing students stay pinned until an explicit opt-in flow (later sub-project).

### Recommendation versioning
`today_focus_history.generator_version text` (`"1.0"` at launch). Persistence + version stamp enable later analysis: "did generator v2 convert better than v1 within the same shape?" without bespoke instrumentation.

## 13. Admin tooling (minimum viable)

Backend: `app/api/v1/endpoints/admin.py` already exists; extended with:
- `GET /admin/students/{id}/inspect` → single JSON: learner profile, all `learner_subjects`, mastery rows, latest Today's Focus, active session (if any) with segment state, last 7 days of session summaries.

Frontend: new `/admin/students/[id]` page — collapsible-sections JSON renderer, read-only. Gated by `Student.is_admin` (new column, defaults false; manually set for founder's account).

Out of scope (later admin sub-project): event timeline, action buttons (reset focus, force-regenerate), student search/list.

Unblocks "my roadmap looks wrong" debugging without DB shell access.

## 14. Testing

### Unit
- Shape selector logic (all 4 shapes triggered correctly given mock student state)
- Readiness % calculation (incl. divide-by-zero when no topics)
- Intent → why-template mapping
- Preferences → system-prompt injection
- Grade-prediction bucketing
- Today's Focus fallback path when generator throws

### Integration (Postgres + Redis test containers)
- Full onboarding wizard end-to-end via API (with diagnostic / with skip / resume from mid-step)
- Diagnostic session writes mastery seeds with expected values
- `today_focus_service` Redis caching + reads + idempotency under simulated dual-device load
- Session resume across simulated reconnect
- Account edit reflects on dashboard

### Migration regression
Fixture loads snapshot of pre-migration data (representative existing users, in-flight sessions, mastery rows). Runs Alembic migration. Asserts:
- Every pre-existing student has ≥1 backfilled `learner_subjects` row matching old flat fields
- Every pre-existing session is resumable: `session_version=1`, `segment_plan` is single-segment, orchestrator load succeeds
- Mastery row count and scores unchanged (no rows lost, no values mutated)
- `Student.preferences` defaults to `{}` (no NULL crashes downstream)

Snapshot lives at `tests/fixtures/pre_migration_v2.sql`.

### Smoke (post-deploy)
Scripted onboarding-then-session through API; assert dashboard payload renders.

### Manual QA checklist
- Onboarding with diagnostic / with skip / resume-from-mid-step
- Dashboard cold (skipped diagnostic) / seeded (took diagnostic) / returning (mock 28d snapshots)
- All 4 session shapes render (debug param forces shape)
- Session leave with progress=0 (instant exit) and >0 (confirm modal copy correct)
- Resume Session card appears after mid-session leave; disappears after completion or 24h auto-close
- Account edit → exam date / target grade / preferences each reflect immediately
- Notification appears after readiness increase, after diagnostic completion
- Stripe upgrade flow still works end-to-end
- Free-tier limit hit mid-segment preserves state + offers upgrade

## 15. Rollout

1. **Backend deploy** (Cloud Run). Migration runs at container startup via existing `start.sh`. Creates new tables, seeds syllabus topics, backfills learner_subjects, adds session columns.
2. **Smoke test** — scripted onboarding-then-session through API.
3. **Seed verification** — explicit checks before frontend flip:
   - `count(syllabus_topics WHERE board='edexcel' AND version='2026.1') > 0`
   - `count(syllabus_topics WHERE board='cambridge' AND version='2026.1') > 0`
   - `count(learner_subjects) >= count(students WHERE onboarding_complete)`
   - Test write+delete to `readiness_snapshots`

   If any fail, `/readyz` is already returning 503 and Cloud Run hasn't swung traffic.
4. **Frontend deploy** (Vercel). New shell live. Flags default `true` for all surfaces.
5. **PostHog flag rollout** — given current user count, 100% immediately. Mechanic exists to flip any surface to 0% in <30s.
6. **48h elevated Sentry threshold** for launch window.
7. **In-flight at deploy time:** existing onboarding drafts (small population) wiped; users restart new wizard. In-flight sessions backfilled to single-segment v2 plan; orchestrator shims; users finish current session normally and get new dashboard on next visit.

### Rollback levers (in order of preference)
1. PostHog flag off per surface (no deploy needed, <30s)
2. Cloud Run revision pin (backend, ~1min)
3. Vercel instant rollback (frontend, ~1min)

Migration is additive (no DROPs); code rollback is safe — old code reads from the retained legacy columns.

## 16. Out of scope (deliberate)

- Push/email notifications (sub-project #5 Engagement)
- Per-topic drill-in pages, Practice mode picker (sub-project #2 Practice)
- Image/PDF upload, exam marking pipeline (sub-project #3 Exam Marker)
- Flashcards + spaced repetition (sub-project #4 Flashcards)
- Real grade-prediction model
- Waitlist capture for unsupported subjects/boards
- "View all" notification history view
- Admin event timeline + action buttons
- Syllabus version opt-in flow for existing students

## 17. Open questions for plan-time

- Exact syllabus topic list for Edexcel 9MA0 vs Cambridge 9709 (need to confirm against current `study_plan_service` data or seed from official spec docs)
- Whether soft-delete account flow exists server-side or needs the placeholder toast
- Stripe webhook handling for `subscription_renewed` notification — confirm existing webhook fires, add `emit_notification` call site
- Mobile breakpoints for full-screen Account edit modals
