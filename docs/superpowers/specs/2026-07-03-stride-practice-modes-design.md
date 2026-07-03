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

Structured as a `planners/` package with a per-mode file and a shared base. This keeps each planner focused and lets future modes (Exam, Past Paper, Timed, Sprint, Mock) be added by dropping a new file and registering it — the dispatcher never changes.

### File layout

```
app/services/planners/
├── __init__.py       # exposes PLANNERS registry
├── base.py           # Planner protocol + shared helpers
├── quick.py          # QuickPlanner
├── weak.py           # WeakAreasPlanner
└── drill.py          # DrillInPlanner
```

### `base.py` — protocol + shared helpers

```python
"""Planner protocol + helpers shared across all practice modes."""
from typing import Protocol, TypedDict
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearnerSubject, MasteryState, SyllabusTopic


class TopicSelection(TypedDict):
    topic: str
    mastery: float | None
    chosen_intent: str | None
    last_practiced_days: int | None
    signal: str  # short machine-readable reason


class PlannerReason(TypedDict):
    topic_selections: list[TopicSelection]


class BuildResult(TypedDict):
    plan: list[dict]     # segment_plan
    reason: PlannerReason


class Planner(Protocol):
    session_type: str
    requires_topic: bool

    async def build(
        self, db: AsyncSession, student_id: UUID, subject: str, topic: str | None
    ) -> BuildResult: ...


# ── shared helpers ─────────────────────────────────────────────────────────────

def _intent_from_mastery(m: float) -> str:
    """Map a mastery score to the pedagogically appropriate intent."""
    if m < 0.20: return "teach"
    if m < 0.60: return "reinforce"
    return "assess"


def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()


async def _validate_topic(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> None:
    """Verify topic exists AND belongs to the student's pinned syllabus for this subject."""
    version_res = await db.execute(
        select(LearnerSubject.syllabus_version).where(
            LearnerSubject.student_id == student_id,
            LearnerSubject.subject == subject,
        )
    )
    version = version_res.scalar()
    if not version:
        raise HTTPException(400, f"Subject '{subject}' not configured for this student")

    res = await db.execute(
        select(SyllabusTopic.topic_id).where(
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
            SyllabusTopic.topic_id == topic,
        ).limit(1)
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(400, f"Topic '{topic}' not in {subject} syllabus {version}")


async def _weakest_topics_with_attempts(
    db: AsyncSession, student_id: UUID, subject: str, limit: int
) -> list[tuple[str, float]]:
    """Return [(topic, mastery)] sorted by mastery ascending, only for topics with attempts."""
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


async def _days_since_last_practice(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> int | None:
    """Days since the topic was last practiced (via last_reviewed_at on mastery)."""
    from datetime import datetime, timezone
    res = await db.execute(
        select(MasteryState.last_reviewed_at)
        .where(MasteryState.student_id == student_id,
               MasteryState.subject == subject,
               MasteryState.topic == topic)
        .limit(1)
    )
    last = res.scalar_one_or_none()
    if not last:
        return None
    return (datetime.now(timezone.utc) - last).days
```

### `quick.py` — QuickPlanner

```python
"""1-segment plan on a user-chosen topic. 3 questions, ~5 min."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.planners.base import (
    BuildResult, PlannerReason, _format_topic, _validate_topic,
)


class QuickPlanner:
    session_type = "quick_practice"
    requires_topic = True

    async def build(
        self, db: AsyncSession, student_id: UUID, subject: str, topic: str | None
    ) -> BuildResult:
        assert topic is not None  # dispatcher already checks requires_topic
        await _validate_topic(db, student_id, subject, topic)

        segment = {
            "idx": 0, "intent": "reinforce", "handler": "practice",
            "topic": topic,
            "why": f"Quick practice on {_format_topic(topic)}.",
            "target_minutes": 5, "status": "in_progress",
            "config": {"mode": "quick_practice", "max_questions": 3, "allow_hints": True},
        }
        reason: PlannerReason = {
            "topic_selections": [{
                "topic": topic, "mastery": None, "chosen_intent": "reinforce",
                "last_practiced_days": None, "signal": "user_selected",
            }],
        }
        return {"plan": [segment], "reason": reason}
```

### `weak.py` — WeakAreasPlanner (adaptive)

```python
"""3-segment plan across 2 weakest topics + mistakes review.

Adaptive intent selection: each segment's intent is derived from the topic's
current mastery (teach < 0.20, reinforce 0.20–0.60, assess ≥ 0.60), so a student
with a near-zero-mastery topic gets a worked example while a student with
partial mastery gets repetition.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.planners.base import (
    BuildResult, PlannerReason, TopicSelection, _first_syllabus_topics,
    _format_topic, _intent_from_mastery, _days_since_last_practice,
    _weakest_topics_with_attempts,
)


class WeakAreasPlanner:
    session_type = "weak_areas"
    requires_topic = False

    async def build(
        self, db: AsyncSession, student_id: UUID, subject: str, topic: str | None
    ) -> BuildResult:
        weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=2)
        # Fresh-student fallback — treat unattempted topics as mastery=0.0 (→ teach intent)
        if len(weak) < 2:
            exclude = {t for t, _ in weak}
            fallback = await _first_syllabus_topics(
                db, student_id, subject, exclude=exclude, limit=2 - len(weak))
            weak = weak + [(t, 0.0) for t in fallback]

        selections: list[TopicSelection] = []
        segments: list[dict] = []
        for i, (topic, mastery) in enumerate(weak):
            intent = _intent_from_mastery(mastery)
            days = await _days_since_last_practice(db, student_id, subject, topic)
            config = {"mode": "weak_areas", "allow_hints": True, "max_questions": 3}
            if intent == "teach":
                config["system_prompt_addendum"] = "Open with a worked example before asking."
            elif intent == "assess":
                config["allow_hints"] = False
                config["max_questions"] = 2
            segments.append({
                "idx": i, "intent": intent, "handler": "practice",
                "topic": topic,
                "why": _why_for(intent, topic, mastery),
                "target_minutes": 6, "status": "in_progress" if i == 0 else "pending",
                "config": config,
            })
            selections.append({
                "topic": topic, "mastery": mastery, "chosen_intent": intent,
                "last_practiced_days": days,
                "signal": _signal_for(i, mastery, days, is_fallback=(mastery == 0.0 and days is None)),
            })

        # Segment 2 — mistakes review (unchanged; always ends the plan)
        segments.append({
            "idx": 2, "intent": "consolidate", "handler": "mistakes",
            "topic": None,
            "why": "Review recent mistakes across your session history.",
            "target_minutes": 3, "status": "pending",
            "config": {"mode": "weak_areas", "source_sessions_days": 7},
        })
        selections.append({
            "topic": "__mistakes__", "mastery": None, "chosen_intent": "consolidate",
            "last_practiced_days": None, "signal": "mistakes_from_recent_sessions",
        })

        return {"plan": segments, "reason": {"topic_selections": selections}}


def _why_for(intent: str, topic: str, mastery: float) -> str:
    name = _format_topic(topic)
    if intent == "teach":
        return f"{name} is nearly unlearned ({int(mastery * 100)}%). Let's build it up."
    if intent == "reinforce":
        return f"{name} is at {int(mastery * 100)}%. Reinforcement time."
    return f"{name} looks solid ({int(mastery * 100)}%). Let's pressure-test it."


def _signal_for(idx: int, mastery: float, days: int | None, is_fallback: bool) -> str:
    if is_fallback:
        return "syllabus_seed_fallback"
    if idx == 0:
        return "weakest_topic_low_mastery" if mastery < 0.20 else "weakest_topic_partial_mastery"
    return "next_weakest"
```

### `drill.py` — DrillInPlanner

```python
"""3-segment plan on ONE topic — teach → reinforce → assess.

Cognitive progression: worked example → guided → independent (no hints).
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.planners.base import (
    BuildResult, PlannerReason, _format_topic, _validate_topic,
)


class DrillInPlanner:
    session_type = "drill_in"
    requires_topic = True

    async def build(
        self, db: AsyncSession, student_id: UUID, subject: str, topic: str | None
    ) -> BuildResult:
        assert topic is not None
        await _validate_topic(db, student_id, subject, topic)
        name = _format_topic(topic)

        segments = [
            {
                "idx": 0, "intent": "teach", "handler": "practice",
                "topic": topic,
                "why": f"Building up {name}.",
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
        reason: PlannerReason = {
            "topic_selections": [{
                "topic": topic, "mastery": None, "chosen_intent": "teach",
                "last_practiced_days": None, "signal": "drill_in_from_dashboard",
            }],
        }
        return {"plan": segments, "reason": reason}
```

### `__init__.py` — registry

```python
"""Practice mode planner registry.

To add a new mode: create a new planner file (following the Planner protocol
in base.py) and register it below. The /sessions/start dispatcher looks up the
planner by session_type — it does not need to change.
"""
from .base import Planner, BuildResult, PlannerReason, TopicSelection
from .quick import QuickPlanner
from .weak import WeakAreasPlanner
from .drill import DrillInPlanner

PLANNERS: dict[str, Planner] = {
    QuickPlanner.session_type: QuickPlanner(),
    WeakAreasPlanner.session_type: WeakAreasPlanner(),
    DrillInPlanner.session_type: DrillInPlanner(),
}

__all__ = ["Planner", "BuildResult", "PlannerReason", "TopicSelection", "PLANNERS"]
```

## 6. `/sessions/start` dispatcher — registry lookup

The dispatcher does not enumerate session types. It looks up the planner by name from the registry — adding a new practice mode is a matter of writing a new planner file and adding it to `PLANNERS`, with zero change here.

```python
from app.services.planners import PLANNERS

resolved_plan: list[dict] = []
planner_reason: dict | None = None

if body.session_type == "diagnostic":
    # existing diagnostic branch (unchanged from sub-project #1)
    resolved_plan = _build_diagnostic_plan(...)
elif body.session_type in PLANNERS:
    planner = PLANNERS[body.session_type]
    if planner.requires_topic and not body.topic:
        raise HTTPException(400, f"topic required for {body.session_type}")
    result = await planner.build(db, student.id, body.subject, body.topic)
    resolved_plan = result["plan"]
    planner_reason = result["reason"]
else:
    # session_type == "practice" — Today's Focus or resumed session; existing behavior
    resolved_plan = body.segment_plan or []
```

`planner_reason` is:
1. Emitted as a `practice_started` PostHog event property (Section 10)
2. Persisted on the `TutorSession.messages` JSON column as a system-role metadata entry with `{"type": "planner_reason", "payload": planner_reason}` so it survives PostHog retention windows and remains available to the admin inspect page

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
| `practice_started` | Backend `POST /sessions/start` succeeds with practice session_type | `mode`, `subject`, `topic` (nullable), **`planner_reason`** (structured; see below) |
| `practice_completed` | Backend orchestrator marks a practice session `session_complete=True` | `mode`, `subject`, `topics_practiced` (list), `duration_sec`, `questions_attempted`, `questions_correct` |
| `weak_topic_tapped` | Frontend: user clicks a tappable weak topic row | `topic`, `mastery_pct` |

### `planner_reason` shape

The `PlannerReason` object built by each planner (see `base.py`) rides on `practice_started` so debugging "why did the planner pick this topic?" becomes queryable in PostHog:

```json
{
  "topic_selections": [
    {"topic": "integration", "mastery": 0.15, "chosen_intent": "teach",
     "last_practiced_days": 21, "signal": "weakest_topic_low_mastery"},
    {"topic": "differentiation", "mastery": 0.48, "chosen_intent": "reinforce",
     "last_practiced_days": 3, "signal": "next_weakest"},
    {"topic": "__mistakes__", "mastery": null, "chosen_intent": "consolidate",
     "last_practiced_days": null, "signal": "mistakes_from_recent_sessions"}
  ]
}
```

Signals used (extensible per-planner):
- `user_selected` — Quick Practice
- `drill_in_from_dashboard` — user tapped a weak topic
- `weakest_topic_low_mastery`, `weakest_topic_partial_mastery`, `next_weakest` — Weak Areas
- `syllabus_seed_fallback` — fresh student without enough attempted topics
- `mistakes_from_recent_sessions` — always used for the mistakes segment of Weak Areas

The same object is persisted to `TutorSession.messages` (see Section 6) so it's available beyond PostHog retention windows.

### Property extensions on existing events

Existing `segment_started` / `segment_completed` / `session_ended` events should include `session_type` in their properties. Sub-project #1's Phase K wiring already passes state properties through — verify these fields are included; add if missing.

## 11. Feature flag

`practice_v2` (PostHog). Default `true`.

- **Frontend:** `<FeatureFlag flag="practice_v2" fallback={null}>` wraps the `<PracticeCard>`. Topics list checks the same flag before rendering rows as tappable buttons vs static list items.
- **Backend:** no flag check. Backend accepts new session_types unconditionally. If frontend flag is off, frontend never sends them. Simpler than plumbing student context into backend flag lookups.

**Rollback:** flip `practice_v2` to false in PostHog → Practice card + tappable topics vanish from dashboard, zero code rollback needed.

## 12. Testing

### Unit tests
Files: `tests/test_planner_base.py`, `tests/test_planner_quick.py`, `tests/test_planner_weak.py`, `tests/test_planner_drill.py`

- `_intent_from_mastery` bucketing: `< 0.20 → teach`, `0.20–0.60 → reinforce`, `≥ 0.60 → assess`, boundary values
- `_validate_topic` raises 400 for unknown topic, for topic not in the student's syllabus_version, for unconfigured subject
- `QuickPlanner.build` returns 1 segment with intent=reinforce, correct config, and `planner_reason.topic_selections[0].signal == "user_selected"`
- `WeakAreasPlanner.build` with student having 2 weak topics at mastery 0.15 + 0.48: intent = [`teach`, `reinforce`, `consolidate`]
- `WeakAreasPlanner.build` fresh-student fallback: 0 attempted topics → 2 syllabus topics seeded, both marked `signal="syllabus_seed_fallback"`, intent = [`teach`, `teach`, `consolidate`]
- `WeakAreasPlanner.build` with 1 attempted topic gets 1 attempted + 1 syllabus (deduplicated)
- `WeakAreasPlanner.build` at mastery 0.65: intent = [`assess`, ...] and `allow_hints=false`, `max_questions=2`
- `DrillInPlanner.build` returns 3 segments all on the given topic with `allow_hints=[True, True, False]`
- Registry: `PLANNERS["quick_practice"] is QuickPlanner()` (or equivalent identity check); all three keys resolve; `PLANNERS` iterable

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

- Exam Mode, Past Paper, Timed Challenge — deferred to a follow-up sub-project (2.5 or later). The registry pattern in Section 6 means adding these is drop-in-a-file.
- Adaptive difficulty within a segment — future.
- Custom question count / target minutes on Quick Practice launch — future.
- Practice-specific analytics dashboard for the student — future.
- Sharing sessions or leaderboards — future.
- Multi-subject picker inside practice modes — waits for multi-subject in general.
- Practice on strong topics (drilling into topics you already know) — non-goal by design.

### Future work explicitly noted (from design brainstorming)

- **Quick Practice "just start" evolution.** Add sibling `QuickPlanner` variants in the registry — `QuickestWeakPlanner` ("continue your weakest unfinished area"), `SurpriseMePlanner` ("random topic in the medium band") — selectable via a small default-mode preference or single-tap default. No engine change; new planner classes only.
- **Cognitive progression rework for Drill-in.** Refine the current `teach → reinforce → assess` (already loosely mapped to worked example → guided → independent) into a richer 4-stage sequence: `worked_example → guided → independent → challenge`. Requires either new segment intents in the enum or refined `system_prompt_addendum` per stage. Design refinement, not urgent.
- **`target_minutes` → `estimated_effort_sec` refactor.** When we have enough real session data to calibrate durations, replace static `target_minutes` on segments with `estimated_effort_sec` and let the frontend format it as time. Cross-cutting change touching all planners + segment schemas + the dashboard's countdown copy — best done as its own small refactor sub-project.
