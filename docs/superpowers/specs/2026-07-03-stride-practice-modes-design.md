# Stride Practice Modes — Sub-project #2

**Status:** Design approved, awaiting implementation plan
**Date:** 2026-07-03
**Author:** Min Thant Tin (with Claude)
**Scope:** Sub-project #2 of 5 in the wider Stride UX overhaul
**Depends on:** Sub-project #1 (shell + onboarding + dashboard + segment engine)

---

## 1. Context

Sub-project #1 shipped the dashboard-first shell with Today's Focus as the daily structured coaching session. Practice modes fill the gap between daily sessions — user-initiated, focused reps.

The original product vision listed 5 modes (Quick, Weak Areas, Exam Mode, Past Paper, Timed Challenge). Sub-project #2 ships 3: **Quick Practice**, **Practice Weak Areas**, **Per-topic drill-in**. Exam Mode / Past Paper / Timed Challenge defer to a follow-up sub-project (2.5 or a later phase) because they need new engine capabilities (timer UI, real past paper Q+MS retrieval, no-hint variants beyond a config flag).

Sub-project #2 is deliberately scoped small — reuses the existing segment engine, no new tables, only 3 mode-planner functions and a small frontend surface addition on the existing dashboard.

## 2. Goals & non-goals

### Goals
1. Users can start a practice session outside of Today's Focus
2. Quick Practice: user picks a topic, gets a fast 1-segment session (3 questions, ~5 min)
3. Weak Areas: auto-picks 2 weakest topics + mistakes review, 3-segment session (~15 min)
4. Per-topic drill-in: click a weak topic on the dashboard → 3-segment session focused on that topic (~10 min)
5. Practice sessions don't clutter Today's Focus semantics — they don't resume, don't appear in the Resume card
6. Feature-flag gated (`practice_v2`) for kill-switch capability

### Non-goals (deliberate)
- Exam Mode (mock paper simulation)
- Past Paper mode (real Q+MS retrieval from Qdrant)
- Timed Challenge mode (countdown + streak)
- Custom question count / difficulty per Quick Practice launch
- Adaptive difficulty within a segment
- Shared/leaderboard features
- Analytics dashboard (view-only reports of practice trends)
- Multi-subject picker inside practice modes (still hardcoded `pure_mathematics` per sub-project #1's MVP)

## 3. Approach

**Approach A from brainstorming — extend `session_type` enum + backend planner service.**

Adds 3 new `session_type` values (`quick_practice`, `weak_areas`, `drill_in`) as first-class dimensions. New `practice_planner.py` service builds the segment plan per mode by composing existing services (mastery, syllabus). `POST /sessions/start` gains a small dispatcher for the new session_types. Existing `practice` handler remains unchanged — segments already carry `topic` + `config` fields that cover every mode's needs.

Rejected alternatives:
- **B — `mode` field inside segment_plan config**: would keep `session_type=practice` for everything but hide the mode inside JSON. Cleaner schema, worse analytics (every event needs to peek at segment_plan JSON to slice by mode).
- **C — frontend builds segment_plan**: fastest, but scatters coaching logic to the client and blocks future non-web clients from reusing it.

## 4. Data model + engine changes

**No SQL migration required.** `TutorSession.session_type` is `String(20)` with no DB-level enum constraint.

### Python-level extensions

**`app/workflows/state.py`** — extend the `session_type` Literal:
```python
session_type: Literal[
    "practice", "diagnostic",
    "quick_practice", "weak_areas", "drill_in",
]
```

**`app/schemas/schemas.py`** — extend `StartSessionRequest.session_type`:
```python
session_type: Literal[
    "practice", "diagnostic",
    "quick_practice", "weak_areas", "drill_in",
] = "practice"
```

### Segment shape (per mode)

Every segment carries a `config.mode` field (`quick_practice` / `weak_areas` / `drill_in`) for analytics traceability. Additional per-segment config flags come from the practice handler's existing surface (`allow_hints`, `max_questions`, `system_prompt_addendum`) — no new handler flags introduced.

The concrete config values per segment appear in Section 5's planner code.

### Backwards compatibility

Existing `session_type="practice"` (Today's Focus) unchanged. `session_type="diagnostic"` (onboarding) unchanged. Only new session types get the new planner branches.

## 5. Practice planner service

**New file:** `app/services/practice_planner.py`

```python
"""Builds segment_plan for practice modes.

Reuses the existing practice / mistakes handlers via segment_plan configuration —
no new handler code needed.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import MasteryState, SyllabusTopic


async def build_quick_practice_plan(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> list[dict]:
    """1-segment plan, 3 questions, on the chosen topic."""
    await _validate_topic(db, subject, topic)
    return [{
        "idx": 0, "intent": "reinforce", "handler": "practice",
        "topic": topic,
        "why": f"Quick practice on {_format_topic(topic)}.",
        "target_minutes": 5, "status": "in_progress",
        "config": {"mode": "quick_practice", "max_questions": 3, "allow_hints": True},
    }]


async def build_weak_areas_plan(
    db: AsyncSession, student_id: UUID, subject: str
) -> list[dict]:
    """3 segments: teach weakest → reinforce 2nd weakest → mistakes review."""
    weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=2)
    # Fallback if student has fewer than 2 attempted topics — pick first syllabus
    # topics that aren't already in the weak list to avoid duplicates.
    if len(weak) < 2:
        exclude = {t for t, _ in weak}
        fallback = await _first_syllabus_topics(
            db, student_id, subject, exclude=exclude, limit=2 - len(weak))
        weak = weak + [(t, 0.0) for t in fallback]

    (t1, m1), (t2, m2) = weak[0], weak[1]
    return [
        {
            "idx": 0, "intent": "teach", "handler": "practice",
            "topic": t1,
            "why": f"Your weakest area — let's build it back up.",
            "target_minutes": 6, "status": "in_progress",
            "config": {"mode": "weak_areas", "target_topics": [t1, t2],
                       "system_prompt_addendum": "Open with a worked example before asking.",
                       "allow_hints": True, "max_questions": 3},
        },
        {
            "idx": 1, "intent": "reinforce", "handler": "practice",
            "topic": t2,
            "why": f"Next-weakest — keep building.",
            "target_minutes": 6, "status": "pending",
            "config": {"mode": "weak_areas", "allow_hints": True, "max_questions": 3},
        },
        {
            "idx": 2, "intent": "consolidate", "handler": "mistakes",
            "topic": None,
            "why": "Review recent mistakes across your session history.",
            "target_minutes": 3, "status": "pending",
            "config": {"mode": "weak_areas", "source_sessions_days": 7},
        },
    ]


async def build_drill_in_plan(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> list[dict]:
    """3 segments on ONE topic: teach → reinforce → assess."""
    await _validate_topic(db, subject, topic)
    return [
        {
            "idx": 0, "intent": "teach", "handler": "practice",
            "topic": topic,
            "why": f"Building up {_format_topic(topic)}.",
            "target_minutes": 4, "status": "in_progress",
            "config": {"mode": "drill_in",
                       "system_prompt_addendum": "Open with a worked example before asking.",
                       "allow_hints": True, "max_questions": 2},
        },
        {
            "idx": 1, "intent": "reinforce", "handler": "practice",
            "topic": topic,
            "why": "Now try something harder.",
            "target_minutes": 4, "status": "pending",
            "config": {"mode": "drill_in", "allow_hints": True, "max_questions": 2},
        },
        {
            "idx": 2, "intent": "assess", "handler": "practice",
            "topic": topic,
            "why": "No hints this round — test what you've learned.",
            "target_minutes": 2, "status": "pending",
            "config": {"mode": "drill_in", "allow_hints": False, "max_questions": 2},
        },
    ]


# ── helpers ────────────────────────────────────────────────────────────────────

async def _weakest_topics_with_attempts(
    db: AsyncSession, student_id: UUID, subject: str, limit: int
) -> list[tuple[str, float]]:
    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(MasteryState.student_id == student_id,
               MasteryState.subject == subject,
               MasteryState.total_attempts > 0)
        .order_by(MasteryState.mastery_score.asc())
        .limit(limit)
    )
    return list(res.all())


async def _first_syllabus_topics(
    db: AsyncSession, student_id: UUID, subject: str, exclude: set[str], limit: int
) -> list[str]:
    """First syllabus topics for the student's pinned syllabus_version, skipping any in `exclude`."""
    from app.db.models import LearnerSubject
    version_res = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = version_res.scalar() or "2026.1"
    res = await db.execute(
        select(SyllabusTopic.topic_id)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.version == version)
        .order_by(SyllabusTopic.ordinal.asc())
    )
    picked: list[str] = []
    for (t,) in res.all():
        if t not in exclude:
            picked.append(t)
            if len(picked) >= limit:
                break
    return picked


async def _validate_topic(db: AsyncSession, subject: str, topic: str) -> None:
    res = await db.execute(
        select(SyllabusTopic.topic_id)
        .where(SyllabusTopic.subject == subject,
               SyllabusTopic.topic_id == topic)
        .limit(1)
    )
    if res.scalar_one_or_none() is None:
        from fastapi import HTTPException
        raise HTTPException(400, f"Unknown topic '{topic}' for subject '{subject}'")


def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()
```

## 6. `/sessions/start` dispatcher

Extend `app/api/v1/endpoints/sessions.py:start_session`:

```python
resolved_plan: list[dict] = []

if body.session_type == "diagnostic":
    # existing diagnostic branch (unchanged from sub-project #1)
    ...
elif body.session_type == "quick_practice":
    if not body.topic:
        raise HTTPException(400, "topic required for quick_practice")
    resolved_plan = await practice_planner.build_quick_practice_plan(
        db, student.id, body.subject, body.topic)
elif body.session_type == "weak_areas":
    resolved_plan = await practice_planner.build_weak_areas_plan(
        db, student.id, body.subject)
elif body.session_type == "drill_in":
    if not body.topic:
        raise HTTPException(400, "topic required for drill_in")
    resolved_plan = await practice_planner.build_drill_in_plan(
        db, student.id, body.subject, body.topic)
else:
    # session_type == "practice" — Today's Focus or resumed session; existing behavior
    resolved_plan = body.segment_plan or []
```

Rest of `start_session` (create TutorSession, initial_state, save_session, telemetry) unchanged.

## 7. New endpoint for Quick Practice dropdown

**New file:** `app/api/v1/endpoints/practice.py`

- `GET /api/v1/practice/topics?subject=pure_mathematics`
- Auth-gated (existing `get_current_student` dependency)
- Returns `list[PracticeTopic]` — Pydantic schema in `app/schemas/practice.py`

**Response shape:**
```python
class PracticeTopic(BaseModel):
    topic_id: str
    topic_name: str
    mastery_pct: int  # 0-100
    has_attempts: bool
```

**Ordering:** attempted topics first (ascending mastery — weakest first), then unattempted syllabus topics in ordinal order. Limit 20 items.

**Router mount** in `app/main.py`: `app.include_router(practice_router, prefix=settings.api_v1_prefix)`.

## 8. Frontend surface

### New Practice card on the dashboard

**File:** `web/src/components/dashboard/practice-card.tsx`

Positioned below Today's Focus / Resume Session, above Recent Activity + Strong/Weak topics.

Structure:
```
Practice
Focused reps between daily sessions.

[Quick Practice]  [Practice Weak Areas]

Or tap a weak topic below to drill in
```

- `[Quick Practice]` opens the Quick Practice modal
- `[Practice Weak Areas]` immediately POSTs `/sessions/start` with `session_type=weak_areas`, routes to `/session/{id}`

### Quick Practice modal

**File:** `web/src/components/dashboard/quick-practice-modal.tsx`

- On open: fetches `practiceApi.getTopics("pure_mathematics")`
- Renders a native `<select>` (functional, no fancy dropdown lib)
- Each option: `{topic_name}` with a mastery badge (e.g., `Integration — 45%`) or `New` badge for unattempted
- `[Cancel]` closes modal
- `[Start]` POSTs `/sessions/start` with `session_type=quick_practice, topic=<selected>`, routes to `/session/{id}`
- Loading state: `Loading topics…` skeleton
- Error state: `Couldn't load topics — retry`

### Weak topics tappable

**File:** `web/src/components/dashboard/topics-list.tsx` (modify)

- Weak-topic rows become `<button>` elements
- On click: POSTs `/sessions/start` with `session_type=drill_in, topic=<row.topic_id>`, routes to `/session/{id}`
- Subtle right-arrow character `→` appears on hover/focus for affordance
- Strong topics remain static (drilling into strong topics is low-value; don't add noise)

### API client

**File:** `web/src/lib/api/practice.ts`

```typescript
import { apiFetch } from "@/lib/api";
import type { PracticeTopic, StartSessionResponse } from "@/lib/types";

export const practiceApi = {
  getTopics: (subject: string) =>
    apiFetch<PracticeTopic[]>(`/practice/topics?subject=${subject}`),
  startQuick: (subject: string, topic: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "quick_practice", topic }),
    }),
  startWeakAreas: (subject: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "weak_areas" }),
    }),
  startDrillIn: (subject: string, topic: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "drill_in", topic }),
    }),
};
```

**Types added to `web/src/lib/types.ts`:**
```typescript
export interface PracticeTopic {
  topic_id: string;
  topic_name: string;
  mastery_pct: number;
  has_attempts: boolean;
}
```

## 9. Session lifecycle

### 1-hour auto-close for practice sessions

Extend the existing cleanup query (currently in `app/api/v1/endpoints/dashboard.py` — auto-closes any active session older than 24h) to differentiate by session_type:

```python
# Stale session auto-close (practice = 1h, other = 24h)
cutoff_practice = datetime.now(timezone.utc) - timedelta(hours=1)
cutoff_default = datetime.now(timezone.utc) - timedelta(hours=24)

stale_sessions = (await db.execute(
    select(TutorSession).where(
        TutorSession.student_id == student.id,
        TutorSession.ended_at.is_(None),
        # Practice modes: 1h; everything else: 24h
        or_(
            and_(TutorSession.session_type.in_(["quick_practice", "weak_areas", "drill_in"]),
                 TutorSession.started_at < cutoff_practice),
            and_(TutorSession.session_type.not_in(["quick_practice", "weak_areas", "drill_in"]),
                 TutorSession.started_at < cutoff_default),
        )
    )
)).scalars().all()

for s in stale_sessions:
    s.ended_at = s.started_at + (timedelta(hours=1) if s.session_type in [...] else timedelta(hours=24))
```

### Resume Session card excludes practice modes

In the same `dashboard.py` endpoint, extend the Resume Session detection query:

```python
rs_row = (await db.execute(
    select(TutorSession).where(
        TutorSession.student_id == student.id,
        TutorSession.subject == subject,
        TutorSession.ended_at.is_(None),
        TutorSession.session_type.in_(["practice", "diagnostic"]),  # exclude practice modes
    ).order_by(TutorSession.started_at.desc())
)).scalars().first()
```

Practice sessions never surface in Resume card even if within their 1h window — they're drop-in/drop-out.

## 10. Observability

### New events

| Event | Fires when | Properties |
|---|---|---|
| `practice_started` | Backend `POST /sessions/start` succeeds with practice session_type | `mode` (quick_practice/weak_areas/drill_in), `subject`, `topic` (nullable) |
| `practice_completed` | Backend orchestrator marks a practice session `session_complete=True` | `mode`, `subject`, `topics_practiced` (list), `duration_sec`, `questions_attempted`, `questions_correct` |
| `weak_topic_tapped` | Frontend: user clicks a tappable weak topic row | `topic`, `mastery_pct` |

### Property extensions on existing events

Existing `segment_started` / `segment_completed` / `session_ended` events should include `session_type` in their properties. Sub-project #1's Phase K wiring already passes state properties through — verify these fields are included; add if missing.

## 11. Feature flag

`practice_v2` (PostHog). Default `true`.

- **Frontend:** `<FeatureFlag flag="practice_v2" fallback={null}>` wraps the `<PracticeCard>`. Topics list checks the same flag before rendering rows as tappable buttons vs static list items.
- **Backend:** no flag check. Backend accepts new session_types unconditionally. If frontend flag is off, frontend never sends them. Simpler than plumbing student context into backend flag lookups.

**Rollback:** flip `practice_v2` to false in PostHog → Practice card + tappable topics vanish from dashboard, zero code rollback needed.

## 12. Testing

### Unit tests
File: `tests/test_practice_planner.py`

- `build_quick_practice_plan` returns 1 segment with correct intent/handler/topic/target_minutes/config
- `build_weak_areas_plan` returns 3 segments: teach → reinforce → mistakes
- `build_weak_areas_plan` fallback: student with 0 attempted topics gets syllabus-seeded plan
- `build_weak_areas_plan` with 1 attempted topic gets 1 attempted + 1 syllabus
- `build_drill_in_plan` returns 3 segments all on the given topic with allow_hints=[T, T, F]
- `_validate_topic` raises 400 on unknown topic

### Integration tests
File: `tests/test_practice_endpoints.py`

- `POST /sessions/start` with `session_type=quick_practice` + valid topic → 201 with 1-segment plan
- `POST /sessions/start` with `session_type=quick_practice` and no `topic` → 400
- `POST /sessions/start` with `session_type=weak_areas` → 201 with 3-segment plan
- `POST /sessions/start` with `session_type=drill_in` + valid topic → 201 with 3-segment plan
- `GET /practice/topics?subject=pure_mathematics` for a student with mastery → attempted-first ordering
- `GET /practice/topics?subject=pure_mathematics` for a fresh student → all `has_attempts=false`
- Auto-close: create a practice session with `started_at=now()-2h`, hit dashboard endpoint, session gets `ended_at`
- Resume filter: create a `session_type=quick_practice` session with `ended_at=None`, hit dashboard, `resume_session` in payload is `None`

### Manual QA checklist

- Fresh student flow: register → skip diagnostic → land on dashboard → Weak Areas launches with syllabus fallback
- Returning student: Weak Areas prioritizes their actual weakest topics
- Quick Practice modal shows attempted topics first, unattempted labeled "New"
- Weak topic tap starts a drill-in immediately (no intermediate modal)
- Practice session leaves you on the session view with segment progress dots
- Leave a practice session idle for >1h, refresh dashboard → no Resume card, session has `ended_at`
- Feature flag off in PostHog → Practice card + tappable rows disappear

## 13. Rollout

**No migration.**

1. Backend build + Cloud Run deploy (per sub-project #1's checklist)
2. Confirm `/readyz` returns 200 (no schema changes; existing check still passes)
3. Frontend push to origin main → Vercel auto-deploys
4. PostHog: create `practice_v2` flag if it doesn't exist, default `true` for all users. Or leave undefined (defaults `true` at client via hook fallback).
5. Manual smoke: walk through Quick / Weak Areas / Drill-in once as a test user.

**Rollback lever priority (same pattern as sub-project #1):**
1. PostHog flag off (`practice_v2 = false`) — no deploy needed, <30s
2. Cloud Run revision pin — backend rollback
3. Vercel instant rollback — frontend rollback

## 14. Out of scope deliberately

- Exam Mode, Past Paper, Timed Challenge — deferred to a follow-up sub-project (2.5 or later)
- Adaptive difficulty within a segment — future
- Custom question count / target minutes on Quick Practice launch — future
- Practice-specific analytics dashboard for the student — future
- Sharing sessions or leaderboards — future
- Multi-subject picker inside practice modes — waits for multi-subject in general
- Practice on strong topics (drilling into topics you already know) — non-goal by design
