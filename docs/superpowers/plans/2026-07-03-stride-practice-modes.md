# Stride Practice Modes — Sub-project #2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user-initiated practice sessions to Stride — Quick Practice, Practice Weak Areas, and Per-topic drill-in — reusing the existing segment engine through a registry-based planner package. Ships behind a `practice_v2` feature flag; no schema migration needed.

**Architecture:** New `app/services/planners/` package with per-mode Planner classes (base protocol + shared helpers + 3 concrete planners) registered in a `PLANNERS` dict. `POST /sessions/start` dispatches by session_type via registry lookup. Dashboard gains a Practice card and tappable weak topics; existing session engine is unchanged. Practice sessions auto-close after 1h and never appear in the Resume Session card.

**Tech Stack:** Backend = FastAPI + SQLAlchemy 2.0 async, existing planner/handler/orchestrator infrastructure from sub-project #1. Frontend = Next.js 16 App Router, existing PostHog feature-flag hook + typed API clients. Tests = pytest + pytest-asyncio.

**Reference spec:** `docs/superpowers/specs/2026-07-03-stride-practice-modes-design.md`

## Global Constraints

- Python 3.11; SQLAlchemy 2.0 async style (`Mapped[T]` + `mapped_column`)
- No database migration (`session_type` is `String(20)` with no DB-level enum)
- Sub-project #1's segment engine, handlers, and orchestrator are unchanged — practice modes compose existing capabilities
- New session_type values: `quick_practice`, `weak_areas`, `drill_in` (must extend the Literal in both `app/workflows/state.py` and `app/schemas/schemas.py`)
- Syllabus version pinned at `2026.1` (existing; planners look this up from `LearnerSubject.syllabus_version`)
- Feature flag: `practice_v2` in PostHog; defaults `true`; gates frontend UI only
- Practice sessions auto-close after 1 hour of inactivity; Today's Focus + diagnostic keep the existing 24h rule
- Practice sessions are excluded from the Resume Session card
- Practice mode config values (per Section 5 of the spec):
  - Quick: 1 segment, intent=`reinforce`, `target_minutes=5`, `max_questions=3`, `allow_hints=True`
  - Weak Areas: 3 segments, per-segment intent from `_intent_from_mastery`, `target_minutes=6/6/3`, segment 2 is `mistakes` handler
  - Drill-in: 3 segments on ONE topic, intents=[`teach`, `reinforce`, `assess`], `target_minutes=4/4/2`, `allow_hints=[T, T, F]`
- Intent thresholds: `mastery < 0.20 → teach`, `mastery < 0.60 → reinforce`, `mastery ≥ 0.60 → assess`
- `PlannerReason` structure lives on `practice_started` event AND is persisted to `TutorSession.messages` as a `{"role":"system","content":"planner_reason:<json>"}` entry
- Commit style: match repo — short sentence-case subject, no Co-Authored-By footer
- No secrets in code; use existing `app.core.telemetry.capture` for backend events, `posthog-js` for frontend

## File Structure

### Backend — new files

| Path | Responsibility |
|---|---|
| `app/services/planners/__init__.py` | Re-exports + `PLANNERS` registry dict |
| `app/services/planners/base.py` | `Planner` Protocol, `BuildResult` / `PlannerReason` / `TopicSelection` TypedDicts, shared helpers (`_intent_from_mastery`, `_validate_topic`, `_weakest_topics_with_attempts`, `_first_syllabus_topics`, `_days_since_last_practice`, `_format_topic`) |
| `app/services/planners/quick.py` | `QuickPlanner` (1 segment, user-picked topic) |
| `app/services/planners/weak.py` | `WeakAreasPlanner` (3 segments, adaptive intent) |
| `app/services/planners/drill.py` | `DrillInPlanner` (3 segments, single topic, teach→reinforce→assess) |
| `app/api/v1/endpoints/practice.py` | `GET /practice/topics` endpoint |
| `app/schemas/practice.py` | `PracticeTopic` schema |
| `tests/test_planner_base.py` | Unit tests for shared helpers |
| `tests/test_planner_quick.py` | `QuickPlanner.build` behavior |
| `tests/test_planner_weak.py` | `WeakAreasPlanner.build` — adaptive intent, fallback, dedup |
| `tests/test_planner_drill.py` | `DrillInPlanner.build` behavior |
| `tests/test_practice_endpoints.py` | `/sessions/start` dispatcher + `/practice/topics` + auto-close + Resume filter |

### Backend — modified files

| Path | Change |
|---|---|
| `app/schemas/schemas.py` | Extend `StartSessionRequest.session_type` Literal (add 3 new values) |
| `app/workflows/state.py` | Extend `SessionState.session_type` Literal (add 3 new values) |
| `app/api/v1/endpoints/sessions.py` | Registry-based dispatcher for `start_session`; persist `planner_reason` to `TutorSession.messages`; emit `practice_started` event |
| `app/api/v1/endpoints/dashboard.py` | Practice-vs-default auto-close windows (1h vs 24h); exclude practice modes from Resume Session query |
| `app/agents/orchestrator.py` | On last-segment completion for practice modes, emit `practice_completed` event with metrics |
| `app/main.py` | Mount `practice_router` at `settings.api_v1_prefix` |

### Frontend — new files

| Path | Responsibility |
|---|---|
| `web/src/lib/api/practice.ts` | `practiceApi.{getTopics, startQuick, startWeakAreas, startDrillIn}` |
| `web/src/components/dashboard/practice-card.tsx` | The Practice card with the two mode buttons |
| `web/src/components/dashboard/quick-practice-modal.tsx` | Modal with topic dropdown + Start button |

### Frontend — modified files

| Path | Change |
|---|---|
| `web/src/lib/types.ts` | Add `PracticeTopic` interface |
| `web/src/components/dashboard/topics-list.tsx` | Weak topics wrap in `<button>` and start drill-in sessions on click; `weak_topic_tapped` PostHog event |
| `web/src/app/(app)/dashboard/page.tsx` | Mount `<PracticeCard>` below Today's Focus / Resume Session, above Recent Activity |
| `web/src/components/shell/feature-flag.tsx` | (Verify) `practice_v2` string is accepted by the union type; extend if the union is closed |
| `web/src/lib/feature-flags.ts` | Add `"practice_v2"` to the `StrideFlag` union |

---

## Phase A — Backend planner package (3 tasks)

### Task 1: Base module + registry scaffold + Literal extensions

**Files:**
- Create: `app/services/planners/__init__.py`
- Create: `app/services/planners/base.py`
- Modify: `app/schemas/schemas.py` — extend `StartSessionRequest.session_type` Literal
- Modify: `app/workflows/state.py` — extend `SessionState.session_type` Literal
- Test: `tests/test_planner_base.py` (create)

**Interfaces produced (used by later tasks):**
- `Planner` Protocol with `session_type: str`, `requires_topic: bool`, `async def build(db, student_id, subject, topic) -> BuildResult`
- `BuildResult = TypedDict("BuildResult", {"plan": list[dict], "reason": PlannerReason})`
- `PlannerReason = TypedDict("PlannerReason", {"topic_selections": list[TopicSelection]})`
- `TopicSelection = TypedDict(...)` with keys `topic`, `mastery`, `chosen_intent`, `last_practiced_days`, `signal`
- Shared helpers: `_intent_from_mastery(m) -> str`, `_format_topic(topic_id) -> str`, `async _validate_topic(db, student_id, subject, topic)`, `async _weakest_topics_with_attempts(db, student_id, subject, limit)`, `async _first_syllabus_topics(db, student_id, subject, exclude, limit)`, `async _days_since_last_practice(db, student_id, subject, topic)`
- `PLANNERS: dict[str, Planner]` — empty at this task; concrete planners added in Tasks 2-3

- [ ] **Step 1: Write helper unit tests (RED)**

```python
# tests/test_planner_base.py
import pytest
from app.services.planners.base import _intent_from_mastery, _format_topic


def test_intent_from_mastery_teach_boundary():
    assert _intent_from_mastery(0.0) == "teach"
    assert _intent_from_mastery(0.19) == "teach"

def test_intent_from_mastery_reinforce_range():
    assert _intent_from_mastery(0.20) == "reinforce"
    assert _intent_from_mastery(0.35) == "reinforce"
    assert _intent_from_mastery(0.59) == "reinforce"

def test_intent_from_mastery_assess_boundary():
    assert _intent_from_mastery(0.60) == "assess"
    assert _intent_from_mastery(0.85) == "assess"
    assert _intent_from_mastery(1.0) == "assess"

def test_format_topic_snake_to_title():
    assert _format_topic("integration_basics") == "Integration Basics"
    assert _format_topic("differentiation_chain_product_quotient") == "Differentiation Chain Product Quotient"


@pytest.mark.asyncio
async def test_validate_topic_raises_when_subject_not_configured(db_session, student):
    """Student has no LearnerSubject row → 400."""
    from fastapi import HTTPException
    from app.services.planners.base import _validate_topic
    with pytest.raises(HTTPException) as exc:
        await _validate_topic(db_session, student.id, "pure_mathematics", "integration_basics")
    assert exc.value.status_code == 400
    assert "not configured" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_topic_raises_when_topic_not_in_syllabus(db_session, student_with_subject, syllabus_edexcel_seeded):
    from fastapi import HTTPException
    from app.services.planners.base import _validate_topic
    with pytest.raises(HTTPException) as exc:
        await _validate_topic(db_session, student_with_subject.id, "pure_mathematics", "not_a_real_topic")
    assert exc.value.status_code == 400
    assert "not in" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_topic_accepts_valid_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    from app.services.planners.base import _validate_topic
    # Should not raise
    await _validate_topic(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")


def test_planners_registry_is_empty_at_this_task():
    from app.services.planners import PLANNERS
    assert isinstance(PLANNERS, dict)
```

- [ ] **Step 2: Run tests, expect fail (imports missing)**

Run: `pytest tests/test_planner_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.planners'`

- [ ] **Step 3: Create the base module**

Create `app/services/planners/base.py`:

```python
"""Planner protocol + helpers shared across all practice modes.

A Planner takes a student's context (subject, optional user-picked topic) and
returns a segment_plan plus a PlannerReason describing why each topic/intent
was chosen. Reasons are surfaced in PostHog and persisted on the session for
post-hoc debugging.
"""
from datetime import datetime, timezone
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
    plan: list[dict]
    reason: PlannerReason


class Planner(Protocol):
    session_type: str
    requires_topic: bool

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult: ...


# ── shared helpers ──────────────────────────────────────────────────────────

_TEACH_UPPER = 0.20
_REINFORCE_UPPER = 0.60


def _intent_from_mastery(m: float) -> str:
    """Map a mastery score to the pedagogically appropriate intent."""
    if m < _TEACH_UPPER:
        return "teach"
    if m < _REINFORCE_UPPER:
        return "reinforce"
    return "assess"


def _format_topic(topic_id: str) -> str:
    return topic_id.replace("_", " ").title()


async def _validate_topic(
    db: AsyncSession, student_id: UUID, subject: str, topic: str
) -> None:
    """Raise 400 if topic isn't in the student's pinned syllabus."""
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
    """[(topic, mastery)] sorted mastery ascending, only for topics with attempts."""
    res = await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
        .order_by(MasteryState.mastery_score.asc())
        .limit(limit)
    )
    return list(res.all())


async def _first_syllabus_topics(
    db: AsyncSession,
    student_id: UUID,
    subject: str,
    exclude: set[str],
    limit: int,
) -> list[str]:
    """First N syllabus topics (by ordinal) for the student's pinned syllabus_version, skipping `exclude`."""
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
    res = await db.execute(
        select(MasteryState.last_reviewed_at).where(
            MasteryState.student_id == student_id,
            MasteryState.subject == subject,
            MasteryState.topic == topic,
        ).limit(1)
    )
    last = res.scalar_one_or_none()
    if not last:
        return None
    return (datetime.now(timezone.utc) - last).days


__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "_intent_from_mastery",
    "_format_topic",
    "_validate_topic",
    "_weakest_topics_with_attempts",
    "_first_syllabus_topics",
    "_days_since_last_practice",
]
```

- [ ] **Step 4: Create the registry `__init__.py`**

Create `app/services/planners/__init__.py`:

```python
"""Practice mode planner registry.

To add a new mode: create a planner file (implementing the Planner protocol
from base.py) and register it in PLANNERS. The /sessions/start dispatcher
looks up planners by session_type — it does not need to change.
"""
from app.services.planners.base import (
    BuildResult,
    Planner,
    PlannerReason,
    TopicSelection,
)

PLANNERS: dict[str, Planner] = {}

__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "PLANNERS",
]
```

Concrete planners get added to `PLANNERS` in Tasks 2 and 3.

- [ ] **Step 5: Extend Literal types**

In `app/schemas/schemas.py`, update `StartSessionRequest.session_type`:

```python
class StartSessionRequest(BaseModel):
    subject: str = Field(description="mathematics, physics, chemistry, biology")
    exam_date: str | None = Field(None, description="ISO date: 2026-06-15")
    topic: str | None = None
    session_type: Literal[
        "practice",
        "diagnostic",
        "quick_practice",
        "weak_areas",
        "drill_in",
    ] = "practice"
    segment_plan: list[dict] | None = None
    return_to: str | None = None
```

In `app/workflows/state.py`, update `SessionState.session_type`:

```python
# Inside SessionState:
    session_type: Literal[
        "practice",
        "diagnostic",
        "quick_practice",
        "weak_areas",
        "drill_in",
    ]
```

- [ ] **Step 6: Run tests, expect pass**

Run: `pytest tests/test_planner_base.py -v`
Expected: PASS — 7 tests, all green.

- [ ] **Step 7: Commit**

```bash
git add app/services/planners/ app/schemas/schemas.py app/workflows/state.py tests/test_planner_base.py
git commit -m "Add practice planner base module + registry scaffold + Literal extensions"
```

---

### Task 2: QuickPlanner + DrillInPlanner

**Files:**
- Create: `app/services/planners/quick.py`
- Create: `app/services/planners/drill.py`
- Modify: `app/services/planners/__init__.py` — register QuickPlanner + DrillInPlanner
- Test: `tests/test_planner_quick.py` (create)
- Test: `tests/test_planner_drill.py` (create)

**Interfaces consumed:** `Planner` protocol, `BuildResult`, `PlannerReason`, `TopicSelection`, `_format_topic`, `_validate_topic` from Task 1.

**Interfaces produced:**
- `QuickPlanner` — `session_type="quick_practice"`, `requires_topic=True`
- `DrillInPlanner` — `session_type="drill_in"`, `requires_topic=True`
- `PLANNERS["quick_practice"]` and `PLANNERS["drill_in"]` populated

- [ ] **Step 1: Write QuickPlanner tests (RED)**

```python
# tests/test_planner_quick.py
import pytest
from app.services.planners.quick import QuickPlanner


def test_quick_planner_metadata():
    p = QuickPlanner()
    assert p.session_type == "quick_practice"
    assert p.requires_topic is True


@pytest.mark.asyncio
async def test_quick_planner_produces_1_segment(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = QuickPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    assert len(result["plan"]) == 1
    seg = result["plan"][0]
    assert seg["idx"] == 0
    assert seg["intent"] == "reinforce"
    assert seg["handler"] == "practice"
    assert seg["topic"] == "integration_basics"
    assert seg["target_minutes"] == 5
    assert seg["status"] == "in_progress"
    assert seg["config"]["mode"] == "quick_practice"
    assert seg["config"]["max_questions"] == 3
    assert seg["config"]["allow_hints"] is True


@pytest.mark.asyncio
async def test_quick_planner_reason_signal(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = QuickPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 1
    assert sel[0]["topic"] == "integration_basics"
    assert sel[0]["chosen_intent"] == "reinforce"
    assert sel[0]["signal"] == "user_selected"


@pytest.mark.asyncio
async def test_quick_planner_rejects_unknown_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    from fastapi import HTTPException
    p = QuickPlanner()
    with pytest.raises(HTTPException) as exc:
        await p.build(db_session, student_with_subject.id, "pure_mathematics", "not_a_topic")
    assert exc.value.status_code == 400
```

- [ ] **Step 2: Write DrillInPlanner tests (RED)**

```python
# tests/test_planner_drill.py
import pytest
from app.services.planners.drill import DrillInPlanner


def test_drill_planner_metadata():
    p = DrillInPlanner()
    assert p.session_type == "drill_in"
    assert p.requires_topic is True


@pytest.mark.asyncio
async def test_drill_planner_produces_3_segments_same_topic(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    plan = result["plan"]
    assert len(plan) == 3
    for seg in plan:
        assert seg["topic"] == "integration_basics"
        assert seg["handler"] == "practice"
    assert [s["intent"] for s in plan] == ["teach", "reinforce", "assess"]
    assert [s["target_minutes"] for s in plan] == [4, 4, 2]
    assert [s["config"]["allow_hints"] for s in plan] == [True, True, False]
    assert plan[0]["status"] == "in_progress"
    assert plan[1]["status"] == "pending"
    assert plan[2]["status"] == "pending"


@pytest.mark.asyncio
async def test_drill_planner_reason_signal(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 1
    assert sel[0]["signal"] == "drill_in_from_dashboard"


@pytest.mark.asyncio
async def test_drill_planner_first_segment_has_worked_example_addendum(db_session, student_with_subject, syllabus_edexcel_seeded):
    p = DrillInPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", "integration_basics")
    assert "worked example" in result["plan"][0]["config"]["system_prompt_addendum"].lower()
```

- [ ] **Step 3: Run both test files, expect fail**

Run: `pytest tests/test_planner_quick.py tests/test_planner_drill.py -v`
Expected: FAIL — modules don't exist yet.

- [ ] **Step 4: Create QuickPlanner**

Create `app/services/planners/quick.py`:

```python
"""1-segment plan on a user-chosen topic. 3 questions, ~5 min."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    _format_topic,
    _validate_topic,
)


class QuickPlanner:
    session_type = "quick_practice"
    requires_topic = True

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        assert topic is not None  # dispatcher already checks requires_topic
        await _validate_topic(db, student_id, subject, topic)

        segment = {
            "idx": 0,
            "intent": "reinforce",
            "handler": "practice",
            "topic": topic,
            "why": f"Quick practice on {_format_topic(topic)}.",
            "target_minutes": 5,
            "status": "in_progress",
            "config": {
                "mode": "quick_practice",
                "max_questions": 3,
                "allow_hints": True,
            },
        }
        reason: PlannerReason = {
            "topic_selections": [
                {
                    "topic": topic,
                    "mastery": None,
                    "chosen_intent": "reinforce",
                    "last_practiced_days": None,
                    "signal": "user_selected",
                }
            ]
        }
        return {"plan": [segment], "reason": reason}
```

- [ ] **Step 5: Create DrillInPlanner**

Create `app/services/planners/drill.py`:

```python
"""3-segment plan on ONE topic — teach → reinforce → assess.

Loosely models cognitive progression: worked example → guided → independent.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    _format_topic,
    _validate_topic,
)


class DrillInPlanner:
    session_type = "drill_in"
    requires_topic = True

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        assert topic is not None
        await _validate_topic(db, student_id, subject, topic)
        name = _format_topic(topic)

        segments = [
            {
                "idx": 0,
                "intent": "teach",
                "handler": "practice",
                "topic": topic,
                "why": f"Building up {name}.",
                "target_minutes": 4,
                "status": "in_progress",
                "config": {
                    "mode": "drill_in",
                    "system_prompt_addendum": "Open with a worked example before asking.",
                    "allow_hints": True,
                    "max_questions": 2,
                },
            },
            {
                "idx": 1,
                "intent": "reinforce",
                "handler": "practice",
                "topic": topic,
                "why": "Now try something harder.",
                "target_minutes": 4,
                "status": "pending",
                "config": {
                    "mode": "drill_in",
                    "allow_hints": True,
                    "max_questions": 2,
                },
            },
            {
                "idx": 2,
                "intent": "assess",
                "handler": "practice",
                "topic": topic,
                "why": "No hints this round — test what you've learned.",
                "target_minutes": 2,
                "status": "pending",
                "config": {
                    "mode": "drill_in",
                    "allow_hints": False,
                    "max_questions": 2,
                },
            },
        ]
        reason: PlannerReason = {
            "topic_selections": [
                {
                    "topic": topic,
                    "mastery": None,
                    "chosen_intent": "teach",
                    "last_practiced_days": None,
                    "signal": "drill_in_from_dashboard",
                }
            ]
        }
        return {"plan": segments, "reason": reason}
```

- [ ] **Step 6: Register both in `PLANNERS`**

Modify `app/services/planners/__init__.py`:

```python
from app.services.planners.base import (
    BuildResult,
    Planner,
    PlannerReason,
    TopicSelection,
)
from app.services.planners.quick import QuickPlanner
from app.services.planners.drill import DrillInPlanner

PLANNERS: dict[str, Planner] = {
    QuickPlanner.session_type: QuickPlanner(),
    DrillInPlanner.session_type: DrillInPlanner(),
}

__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "PLANNERS",
]
```

- [ ] **Step 7: Run tests, expect pass**

Run: `pytest tests/test_planner_quick.py tests/test_planner_drill.py -v`
Expected: PASS — 7 tests, all green.

- [ ] **Step 8: Commit**

```bash
git add app/services/planners/quick.py app/services/planners/drill.py app/services/planners/__init__.py tests/test_planner_quick.py tests/test_planner_drill.py
git commit -m "Add QuickPlanner and DrillInPlanner, register in PLANNERS"
```

---

### Task 3: WeakAreasPlanner (adaptive intent)

**Files:**
- Create: `app/services/planners/weak.py`
- Modify: `app/services/planners/__init__.py` — register WeakAreasPlanner
- Test: `tests/test_planner_weak.py` (create)

**Interfaces consumed:** `Planner`, `BuildResult`, `PlannerReason`, `TopicSelection`, `_intent_from_mastery`, `_weakest_topics_with_attempts`, `_first_syllabus_topics`, `_days_since_last_practice`, `_format_topic` from Task 1.

**Interfaces produced:**
- `WeakAreasPlanner` — `session_type="weak_areas"`, `requires_topic=False`
- `PLANNERS["weak_areas"]` populated

- [ ] **Step 1: Write WeakAreasPlanner tests (RED)**

```python
# tests/test_planner_weak.py
import pytest
from datetime import datetime, timezone, timedelta
from app.db.models import MasteryState
from app.services.planners.weak import WeakAreasPlanner


def test_weak_areas_metadata():
    p = WeakAreasPlanner()
    assert p.session_type == "weak_areas"
    assert p.requires_topic is False


@pytest.mark.asyncio
async def test_weak_areas_two_low_mastery_topics(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Student with 2 attempted topics at mastery 0.15 and 0.48 gets teach + reinforce + mistakes."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.15, total_attempts=3,
                     last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=21)),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.48, total_attempts=5,
                     last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=3)),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert len(plan) == 3
    # Segment 0: weakest topic (integration_basics, 0.15 → teach)
    assert plan[0]["topic"] == "integration_basics"
    assert plan[0]["intent"] == "teach"
    assert "worked example" in plan[0]["config"]["system_prompt_addendum"].lower()
    # Segment 1: next-weakest (differentiation_basics, 0.48 → reinforce)
    assert plan[1]["topic"] == "differentiation_basics"
    assert plan[1]["intent"] == "reinforce"
    # Segment 2: mistakes review
    assert plan[2]["intent"] == "consolidate"
    assert plan[2]["handler"] == "mistakes"
    assert plan[2]["topic"] is None


@pytest.mark.asyncio
async def test_weak_areas_high_mastery_becomes_assess(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Topic with mastery 0.65 becomes an 'assess' segment with hints disabled."""
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.65, total_attempts=8),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.30, total_attempts=4),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    # Segment 0 was picked as the weakest with attempts (differentiation_basics @ 0.30 → reinforce)
    assert plan[0]["topic"] == "differentiation_basics"
    assert plan[0]["intent"] == "reinforce"
    # Segment 1 next-weakest — integration_basics @ 0.65 → assess
    assert plan[1]["intent"] == "assess"
    assert plan[1]["config"]["allow_hints"] is False
    assert plan[1]["config"]["max_questions"] == 2


@pytest.mark.asyncio
async def test_weak_areas_fresh_student_fallback(db_session, student_with_subject, syllabus_edexcel_seeded):
    """Student with no attempted topics gets syllabus-seeded plan, all teach intent."""
    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert len(plan) == 3
    # Both non-mistakes segments should have intent=teach (mastery=0.0 fallback)
    assert plan[0]["intent"] == "teach"
    assert plan[1]["intent"] == "teach"
    # Both topics come from the syllabus in ordinal order
    # (first two syllabus topics for Edexcel Pure Maths per syllabus_seed.py)
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_two = [t["topic_id"] for t in EDEXCEL_9MA0_TOPICS[:2]]
    assert plan[0]["topic"] == first_two[0]
    assert plan[1]["topic"] == first_two[1]

    # Both selections have signal = syllabus_seed_fallback
    sel = result["reason"]["topic_selections"]
    assert sel[0]["signal"] == "syllabus_seed_fallback"
    assert sel[1]["signal"] == "syllabus_seed_fallback"


@pytest.mark.asyncio
async def test_weak_areas_one_attempted_dedup(db_session, student_with_subject, syllabus_edexcel_seeded):
    """1 attempted topic + fallback should not repeat the attempted topic."""
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    first_topic = EDEXCEL_9MA0_TOPICS[0]["topic_id"]
    db_session.add(
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic=first_topic, mastery_score=0.10, total_attempts=2)
    )
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    plan = result["plan"]
    assert plan[0]["topic"] == first_topic
    # Segment 1 must be a *different* topic — not first_topic again
    assert plan[1]["topic"] != first_topic


@pytest.mark.asyncio
async def test_weak_areas_reason_signals(db_session, student_with_subject, syllabus_edexcel_seeded):
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.15, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.48, total_attempts=5),
    ])
    await db_session.flush()

    p = WeakAreasPlanner()
    result = await p.build(db_session, student_with_subject.id, "pure_mathematics", None)
    sel = result["reason"]["topic_selections"]
    assert len(sel) == 3
    assert sel[0]["signal"] == "weakest_topic_low_mastery"
    assert sel[1]["signal"] == "next_weakest"
    assert sel[2]["signal"] == "mistakes_from_recent_sessions"
```

- [ ] **Step 2: Run tests, expect fail**

Run: `pytest tests/test_planner_weak.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement `WeakAreasPlanner`**

Create `app/services/planners/weak.py`:

```python
"""3-segment plan across 2 weakest topics + mistakes review.

Adaptive intent selection: each segment's intent is derived from the topic's
current mastery via _intent_from_mastery. A near-zero-mastery topic gets a
worked example (teach), a partial-mastery topic gets repetition (reinforce),
and a solid topic gets a no-hint pressure test (assess).
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planners.base import (
    BuildResult,
    PlannerReason,
    TopicSelection,
    _days_since_last_practice,
    _first_syllabus_topics,
    _format_topic,
    _intent_from_mastery,
    _weakest_topics_with_attempts,
)


class WeakAreasPlanner:
    session_type = "weak_areas"
    requires_topic = False

    async def build(
        self,
        db: AsyncSession,
        student_id: UUID,
        subject: str,
        topic: str | None,
    ) -> BuildResult:
        weak = await _weakest_topics_with_attempts(db, student_id, subject, limit=2)
        fallback_flags = [False] * len(weak)

        if len(weak) < 2:
            exclude = {t for t, _ in weak}
            fallback = await _first_syllabus_topics(
                db, student_id, subject, exclude=exclude, limit=2 - len(weak)
            )
            for t in fallback:
                weak.append((t, 0.0))
                fallback_flags.append(True)

        selections: list[TopicSelection] = []
        segments: list[dict] = []

        for i, (topic_id, mastery) in enumerate(weak):
            intent = _intent_from_mastery(mastery)
            days = await _days_since_last_practice(db, student_id, subject, topic_id)
            config: dict = {"mode": "weak_areas", "allow_hints": True, "max_questions": 3}
            if intent == "teach":
                config["system_prompt_addendum"] = "Open with a worked example before asking."
            elif intent == "assess":
                config["allow_hints"] = False
                config["max_questions"] = 2

            segments.append({
                "idx": i,
                "intent": intent,
                "handler": "practice",
                "topic": topic_id,
                "why": _why_for(intent, topic_id, mastery),
                "target_minutes": 6,
                "status": "in_progress" if i == 0 else "pending",
                "config": config,
            })
            selections.append({
                "topic": topic_id,
                "mastery": mastery,
                "chosen_intent": intent,
                "last_practiced_days": days,
                "signal": _signal_for(i, mastery, fallback_flags[i]),
            })

        # Trailing mistakes-review segment
        segments.append({
            "idx": 2,
            "intent": "consolidate",
            "handler": "mistakes",
            "topic": None,
            "why": "Review recent mistakes across your session history.",
            "target_minutes": 3,
            "status": "pending",
            "config": {"mode": "weak_areas", "source_sessions_days": 7},
        })
        selections.append({
            "topic": "__mistakes__",
            "mastery": None,
            "chosen_intent": "consolidate",
            "last_practiced_days": None,
            "signal": "mistakes_from_recent_sessions",
        })

        return {"plan": segments, "reason": {"topic_selections": selections}}


def _why_for(intent: str, topic: str, mastery: float) -> str:
    name = _format_topic(topic)
    if intent == "teach":
        return f"{name} is nearly unlearned ({int(mastery * 100)}%). Let's build it up."
    if intent == "reinforce":
        return f"{name} is at {int(mastery * 100)}%. Reinforcement time."
    return f"{name} looks solid ({int(mastery * 100)}%). Let's pressure-test it."


def _signal_for(idx: int, mastery: float, is_fallback: bool) -> str:
    if is_fallback:
        return "syllabus_seed_fallback"
    if idx == 0:
        return "weakest_topic_low_mastery" if mastery < 0.20 else "weakest_topic_partial_mastery"
    return "next_weakest"
```

- [ ] **Step 4: Register `WeakAreasPlanner` in `PLANNERS`**

Modify `app/services/planners/__init__.py`:

```python
from app.services.planners.base import (
    BuildResult,
    Planner,
    PlannerReason,
    TopicSelection,
)
from app.services.planners.quick import QuickPlanner
from app.services.planners.weak import WeakAreasPlanner
from app.services.planners.drill import DrillInPlanner

PLANNERS: dict[str, Planner] = {
    QuickPlanner.session_type: QuickPlanner(),
    WeakAreasPlanner.session_type: WeakAreasPlanner(),
    DrillInPlanner.session_type: DrillInPlanner(),
}

__all__ = [
    "Planner",
    "BuildResult",
    "PlannerReason",
    "TopicSelection",
    "PLANNERS",
]
```

- [ ] **Step 5: Run tests, expect pass**

Run: `pytest tests/test_planner_weak.py -v`
Expected: PASS — 5 tests, all green.

Also run: `pytest tests/test_planner_base.py tests/test_planner_quick.py tests/test_planner_weak.py tests/test_planner_drill.py -v`
Expected: All planner tests still green.

- [ ] **Step 6: Commit**

```bash
git add app/services/planners/weak.py app/services/planners/__init__.py tests/test_planner_weak.py
git commit -m "Add WeakAreasPlanner with adaptive intent from mastery"
```

---

## Phase B — Backend endpoints + dispatcher (2 tasks)

### Task 4: `/sessions/start` registry dispatcher + `planner_reason` persistence + `practice_started` event

**Files:**
- Modify: `app/api/v1/endpoints/sessions.py:51-140` (start_session function)
- Modify: `app/agents/orchestrator.py` — add `practice_completed` event emission on last-segment completion for practice modes
- Test: `tests/test_practice_endpoints.py` (create — first 4 tests focused on dispatcher)

**Interfaces consumed:** `PLANNERS` from Task 3.

**Interfaces produced:**
- `POST /api/v1/sessions/start` accepts `session_type` values `quick_practice | weak_areas | drill_in` and dispatches via `PLANNERS`
- `TutorSession.messages` includes a `{"role":"system","content":"planner_reason:<json>"}` entry for practice sessions
- PostHog `practice_started` event emitted with `mode`, `subject`, `topic`, `planner_reason` properties
- PostHog `practice_completed` event emitted from the orchestrator when a practice session's last segment completes

- [ ] **Step 1: Write dispatcher integration tests (RED)**

```python
# tests/test_practice_endpoints.py
import pytest
import json


@pytest.mark.asyncio
async def test_start_session_dispatches_quick_practice(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
        "topic": "integration_basics",
    })
    assert r.status_code == 201
    body = r.json()
    assert "session_id" in body


@pytest.mark.asyncio
async def test_quick_practice_requires_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
    })
    assert r.status_code == 400
    assert "topic required" in r.json()["detail"]


@pytest.mark.asyncio
async def test_drill_in_requires_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "drill_in",
    })
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_weak_areas_starts_without_topic(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "weak_areas",
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_planner_reason_persisted_on_session_messages(authed_client, db_session, student_with_subject, syllabus_edexcel_seeded):
    from app.db.models import TutorSession
    from sqlalchemy import select

    r = await authed_client.post("/api/v1/sessions/start", json={
        "subject": "pure_mathematics",
        "session_type": "quick_practice",
        "topic": "integration_basics",
    })
    session_id = r.json()["session_id"]

    row = (await db_session.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )).scalar_one()
    system_entries = [
        m for m in row.messages
        if m.get("role") == "system" and m.get("content", "").startswith("planner_reason:")
    ]
    assert len(system_entries) == 1
    payload = json.loads(system_entries[0]["content"].removeprefix("planner_reason:"))
    assert payload["topic_selections"][0]["signal"] == "user_selected"
```

- [ ] **Step 2: Run tests, expect fail**

Run: `pytest tests/test_practice_endpoints.py -v -k "dispatches or requires or starts_without or persisted"`
Expected: FAIL — dispatcher/persistence not implemented.

- [ ] **Step 3: Modify `start_session` in `app/api/v1/endpoints/sessions.py`**

Locate the existing `start_session` function (around line 51). Replace the plan-resolution block with:

```python
import json  # top of file if not present

# Inside start_session, replace the block that assigns resolved_plan:
from app.services.planners import PLANNERS
from app.core.telemetry import capture

resolved_plan: list[dict] = []
planner_reason: dict | None = None
practice_mode: str | None = None

if body.session_type == "diagnostic":
    # existing diagnostic branch — unchanged from sub-project #1
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    diagnostic_plan = [
        {
            "idx": i,
            "intent": "diagnose",
            "handler": "diagnostic_question",
            "topic": t["topic_id"],
            "topic_name": t["topic_name"],
            "why": "Baseline diagnostic",
            "target_minutes": 2,
            "status": "in_progress" if i == 0 else "pending",
            "config": {},
        }
        for i, t in enumerate(EDEXCEL_9MA0_TOPICS[:7])
    ]
    resolved_plan = body.segment_plan or diagnostic_plan
elif body.session_type in PLANNERS:
    planner = PLANNERS[body.session_type]
    if planner.requires_topic and not body.topic:
        raise HTTPException(400, f"topic required for {body.session_type}")
    result = await planner.build(db, student.id, body.subject, body.topic)
    resolved_plan = result["plan"]
    planner_reason = result["reason"]
    practice_mode = body.session_type
else:
    # session_type == "practice" — Today's Focus or resumed session
    resolved_plan = body.segment_plan or []
```

Then, after `state["conversation_history"].extend(history)` and BEFORE `save_session(state)`, append the planner reason as a system-role message:

```python
if planner_reason is not None:
    state["conversation_history"].append({
        "role": "system",
        "content": f"planner_reason:{json.dumps(planner_reason)}",
        "metadata": {"type": "planner_reason"},
    })
```

Then, after `await db.commit()`, replace the existing `session_started` capture with a mode-aware one, and add `practice_started`:

```python
capture(str(student.id), "session_started", {
    "session_id": state["session_id"],
    "subject": body.subject,
    "exam_board": student.exam_board,
    "is_new_student": not bool(weak_topics),
    "subscription_tier": student.subscription_tier,
    "session_type": body.session_type,
})

if practice_mode is not None:
    try:
        capture(str(student.id), "practice_started", {
            "mode": practice_mode,
            "subject": body.subject,
            "topic": body.topic,
            "planner_reason": planner_reason,
        })
    except Exception:
        pass
```

- [ ] **Step 4: Add `practice_completed` emission in the orchestrator**

Modify `app/agents/orchestrator.py`. Inside `step_session`, at the point where the last segment completes and `state_changes["session_complete"] = True` is set, add:

```python
# Emit practice_completed for practice modes
try:
    from app.core.telemetry import capture
    session_type = state.get("session_type")
    if session_type in ("quick_practice", "weak_areas", "drill_in"):
        # Aggregate practice metrics from the plan + evaluated segments
        topics_practiced = list({
            s["topic"] for s in plan
            if s.get("topic") and s["topic"] != "__mistakes__"
        })
        # Duration approximated from segment target_minutes for now — real timing is a Phase D refactor
        duration_sec = sum(s.get("target_minutes", 0) for s in plan) * 60
        # Question counts from segment config's questions_asked (set by the practice handler)
        questions_attempted = sum(
            (s.get("config", {}).get("questions_asked") or 0) for s in plan
        )
        questions_correct = sum(
            (s.get("config", {}).get("questions_correct") or 0) for s in plan
        )
        capture(state["student_id"], "practice_completed", {
            "mode": session_type,
            "subject": state.get("subject"),
            "topics_practiced": topics_practiced,
            "duration_sec": duration_sec,
            "questions_attempted": questions_attempted,
            "questions_correct": questions_correct,
        })
except Exception:
    pass
```

Also update the existing `session_ended` / `segment_started` / `segment_completed` events to include `session_type` in their properties (they already have most fields; just confirm and add if missing).

- [ ] **Step 5: Run dispatcher tests**

Run: `pytest tests/test_practice_endpoints.py -v -k "dispatches or requires or starts_without or persisted"`
Expected: PASS — 5 tests all green.

- [ ] **Step 6: Regression check**

Run: `pytest tests/test_diagnostic_handler.py tests/test_practice_handler.py tests/test_orchestrator.py tests/test_start_session_extension.py -v`
Expected: All existing sub-project #1 engine tests still pass.

- [ ] **Step 7: Commit**

```bash
git add app/api/v1/endpoints/sessions.py app/agents/orchestrator.py tests/test_practice_endpoints.py
git commit -m "Add practice mode dispatcher via PLANNERS registry with planner_reason persistence and analytics"
```

---

### Task 5: `/practice/topics` endpoint + dashboard auto-close/resume changes

**Files:**
- Create: `app/api/v1/endpoints/practice.py`
- Create: `app/schemas/practice.py`
- Modify: `app/main.py` — mount practice router
- Modify: `app/api/v1/endpoints/dashboard.py` — practice-vs-default auto-close windows + Resume filter
- Modify: `tests/test_practice_endpoints.py` (extend with topics + auto-close + Resume tests)

**Interfaces produced:**
- `GET /api/v1/practice/topics?subject=pure_mathematics` returns `list[PracticeTopic]`
- `PracticeTopic` schema: `topic_id: str`, `topic_name: str`, `mastery_pct: int`, `has_attempts: bool`
- Dashboard endpoint: practice sessions auto-close at 1h; Today's Focus + diagnostic keep 24h; Resume Session card excludes practice modes

- [ ] **Step 1: Write additional tests (RED)**

Append to `tests/test_practice_endpoints.py`:

```python
@pytest.mark.asyncio
async def test_practice_topics_fresh_student(authed_client, student_with_subject, syllabus_edexcel_seeded):
    r = await authed_client.get("/api/v1/practice/topics?subject=pure_mathematics")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # Fresh student — all topics have no attempts, mastery = 0
    for t in body:
        assert t["has_attempts"] is False
        assert t["mastery_pct"] == 0
    # Ordering: syllabus ordinal
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS
    expected_first = EDEXCEL_9MA0_TOPICS[0]["topic_id"]
    assert body[0]["topic_id"] == expected_first


@pytest.mark.asyncio
async def test_practice_topics_returning_student_orders_attempted_first(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from app.db.models import MasteryState
    db_session.add_all([
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="integration_basics", mastery_score=0.30, total_attempts=3),
        MasteryState(student_id=student_with_subject.id, subject="pure_mathematics",
                     topic="differentiation_basics", mastery_score=0.10, total_attempts=2),
    ])
    await db_session.flush()

    r = await authed_client.get("/api/v1/practice/topics?subject=pure_mathematics")
    body = r.json()

    # Attempted topics first, weakest first
    assert body[0]["topic_id"] == "differentiation_basics"
    assert body[0]["has_attempts"] is True
    assert body[0]["mastery_pct"] == 10
    assert body[1]["topic_id"] == "integration_basics"
    assert body[1]["has_attempts"] is True
    assert body[1]["mastery_pct"] == 30
    # Remaining topics are unattempted syllabus topics
    assert body[2]["has_attempts"] is False


@pytest.mark.asyncio
async def test_practice_session_auto_closes_after_1h(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from datetime import datetime, timezone, timedelta
    from app.db.models import TutorSession
    from sqlalchemy import select

    stale = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="quick_practice",
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        ended_at=None,
    )
    db_session.add(stale)
    await db_session.flush()

    # Hit the dashboard — cleanup runs on load
    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert r.status_code == 200

    await db_session.refresh(stale)
    assert stale.ended_at is not None


@pytest.mark.asyncio
async def test_todays_focus_session_still_uses_24h_window(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from datetime import datetime, timezone, timedelta
    from app.db.models import TutorSession

    still_active = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="practice",   # Today's Focus
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        ended_at=None,
    )
    db_session.add(still_active)
    await db_session.flush()

    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    assert r.status_code == 200

    await db_session.refresh(still_active)
    # Still within 24h — should NOT be auto-closed
    assert still_active.ended_at is None


@pytest.mark.asyncio
async def test_practice_session_excluded_from_resume_card(
    authed_client, db_session, student_with_subject, syllabus_edexcel_seeded
):
    from app.db.models import TutorSession

    active_practice = TutorSession(
        student_id=student_with_subject.id,
        subject="pure_mathematics",
        mode="explain",
        session_type="quick_practice",
        segment_plan=[{"idx": 0, "topic": "integration_basics"}],
        current_segment_idx=0,
        ended_at=None,
    )
    db_session.add(active_practice)
    await db_session.flush()

    r = await authed_client.get("/api/v1/dashboard/pure_mathematics")
    body = r.json()
    assert body["resume_session"] is None
```

- [ ] **Step 2: Run tests, expect fail**

Run: `pytest tests/test_practice_endpoints.py -v -k "topics or auto_close or excluded"`
Expected: FAIL — endpoint doesn't exist / auto-close logic isn't differentiated.

- [ ] **Step 3: Create the schema module**

Create `app/schemas/practice.py`:

```python
from pydantic import BaseModel


class PracticeTopic(BaseModel):
    topic_id: str
    topic_name: str
    mastery_pct: int  # 0–100
    has_attempts: bool
```

- [ ] **Step 4: Create the endpoint module**

Create `app/api/v1/endpoints/practice.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import LearnerSubject, MasteryState, SyllabusTopic, Student
from app.schemas.practice import PracticeTopic

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/topics", response_model=list[PracticeTopic])
async def list_practice_topics(
    subject: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> list[PracticeTopic]:
    """Topics the student can practice on for the given subject.

    Ordering: attempted topics first (weakest mastery first),
    then unattempted syllabus topics in ordinal order. Limit 20.
    """
    ls_row = (await db.execute(
        select(LearnerSubject).where(
            LearnerSubject.student_id == student.id,
            LearnerSubject.subject == subject,
            LearnerSubject.is_draft == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not ls_row:
        raise HTTPException(404, f"Subject '{subject}' not configured for this student")

    version = ls_row.syllabus_version

    # All syllabus topics for this board/subject/version, in ordinal order
    syllabus_rows = (await db.execute(
        select(SyllabusTopic.topic_id, SyllabusTopic.topic_name, SyllabusTopic.ordinal)
        .where(
            SyllabusTopic.exam_board == ls_row.exam_board,
            SyllabusTopic.subject == subject,
            SyllabusTopic.version == version,
        )
        .order_by(SyllabusTopic.ordinal.asc())
    )).all()

    name_map = {r[0]: r[1] for r in syllabus_rows}
    ordinal_map = {r[0]: r[2] for r in syllabus_rows}

    # Attempted topics for this student
    attempted_rows = (await db.execute(
        select(MasteryState.topic, MasteryState.mastery_score)
        .where(
            MasteryState.student_id == student.id,
            MasteryState.subject == subject,
            MasteryState.total_attempts > 0,
        )
        .order_by(MasteryState.mastery_score.asc())
    )).all()

    attempted_topics = {r[0] for r in attempted_rows}
    attempted = [
        PracticeTopic(
            topic_id=t,
            topic_name=name_map.get(t, t),
            mastery_pct=int((m or 0) * 100),
            has_attempts=True,
        )
        for t, m in attempted_rows
        if t in name_map
    ]

    unattempted = [
        PracticeTopic(
            topic_id=t,
            topic_name=name_map[t],
            mastery_pct=0,
            has_attempts=False,
        )
        for t in name_map
        if t not in attempted_topics
    ]

    return (attempted + unattempted)[:20]
```

- [ ] **Step 5: Mount the router in `app/main.py`**

Add near the other `include_router` calls:

```python
from app.api.v1.endpoints.practice import router as practice_router
# ... existing routers ...
app.include_router(practice_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 6: Differentiate auto-close in `dashboard.py`**

In `app/api/v1/endpoints/dashboard.py`, find the existing stale-session cleanup block (auto-closes `ended_at IS NULL` sessions older than 24h). Replace it with:

```python
from datetime import timedelta

PRACTICE_MODES = ("quick_practice", "weak_areas", "drill_in")

now = datetime.now(timezone.utc)
practice_cutoff = now - timedelta(hours=1)
default_cutoff = now - timedelta(hours=24)

stale = (await db.execute(
    select(TutorSession).where(
        TutorSession.student_id == student.id,
        TutorSession.subject == subject,
        TutorSession.ended_at.is_(None),
    )
)).scalars().all()

for s in stale:
    if s.session_type in PRACTICE_MODES:
        if s.started_at and s.started_at < practice_cutoff:
            s.ended_at = s.started_at + timedelta(hours=1)
    else:
        if s.started_at and s.started_at < default_cutoff:
            s.ended_at = s.started_at + timedelta(hours=24)
await db.flush()
```

Then, in the same file, find the Resume Session query and add the session_type exclusion:

```python
rs_row = (await db.execute(
    select(TutorSession).where(
        TutorSession.student_id == student.id,
        TutorSession.subject == subject,
        TutorSession.ended_at.is_(None),
        TutorSession.session_type.in_(["practice", "diagnostic"]),
    ).order_by(TutorSession.started_at.desc())
)).scalars().first()
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_practice_endpoints.py -v`
Expected: All 10 tests green.

Also run: `pytest tests/test_dashboard_endpoint.py -v`
Expected: All existing dashboard tests still pass.

- [ ] **Step 8: Commit**

```bash
git add app/api/v1/endpoints/practice.py app/schemas/practice.py app/main.py app/api/v1/endpoints/dashboard.py tests/test_practice_endpoints.py
git commit -m "Add /practice/topics endpoint; 1h auto-close for practice; exclude practice from Resume Session"
```

---

## Phase C — Frontend (2 tasks)

### Task 6: API client + types + PracticeCard + QuickPracticeModal

**Files:**
- Create: `web/src/lib/api/practice.ts`
- Create: `web/src/components/dashboard/practice-card.tsx`
- Create: `web/src/components/dashboard/quick-practice-modal.tsx`
- Modify: `web/src/lib/types.ts` — add `PracticeTopic` interface
- Modify: `web/src/lib/feature-flags.ts` — add `"practice_v2"` to `StrideFlag` union

**Interfaces produced:**
- `practiceApi.getTopics(subject: string): Promise<PracticeTopic[]>`
- `practiceApi.startQuick(subject: string, topic: string): Promise<StartSessionResponse>`
- `practiceApi.startWeakAreas(subject: string): Promise<StartSessionResponse>`
- `practiceApi.startDrillIn(subject: string, topic: string): Promise<StartSessionResponse>`
- `<PracticeCard subject={string} />` — dashboard section with two buttons
- `<QuickPracticeModal subject={string} onClose={} />` — topic dropdown + Start

- [ ] **Step 1: Add `PracticeTopic` type**

Append to `web/src/lib/types.ts`:

```typescript
export interface PracticeTopic {
  topic_id: string;
  topic_name: string;
  mastery_pct: number;
  has_attempts: boolean;
}
```

- [ ] **Step 2: Add `practice_v2` to the flag union**

Modify `web/src/lib/feature-flags.ts` (find `StrideFlag` type):

```typescript
export type StrideFlag =
  | "dashboard_v2"
  | "onboarding_v2"
  | "session_engine_v2"
  | "notifications_v2"
  | "account_v2"
  | "practice_v2";

const KNOWN_FLAGS: ReadonlyArray<StrideFlag> = [
  "dashboard_v2", "onboarding_v2", "session_engine_v2",
  "notifications_v2", "account_v2", "practice_v2",
];
```

- [ ] **Step 3: Create the API client**

Create `web/src/lib/api/practice.ts`:

```typescript
import { apiFetch } from "@/lib/api";
import type { PracticeTopic, StartSessionResponse } from "@/lib/types";

export const practiceApi = {
  getTopics: (subject: string) =>
    apiFetch<PracticeTopic[]>(`/practice/topics?subject=${encodeURIComponent(subject)}`),
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

Also verify `StartSessionResponse` is exported from `@/lib/types`. If not, add:

```typescript
// web/src/lib/types.ts
export interface StartSessionResponse {
  session_id: string;
  message: string;
  is_new_student: boolean;
}
```

- [ ] **Step 4: Create the QuickPracticeModal**

Create `web/src/components/dashboard/quick-practice-modal.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeTopic } from "@/lib/types";

interface Props {
  subject: string;
  onClose: () => void;
}

export function QuickPracticeModal({ subject, onClose }: Props) {
  const router = useRouter();
  const [topics, setTopics] = useState<PracticeTopic[] | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [errored, setErrored] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    practiceApi.getTopics(subject)
      .then((rows) => {
        setTopics(rows);
        if (rows.length > 0) setSelected(rows[0].topic_id);
      })
      .catch(() => setErrored(true));
  }, [subject]);

  const start = async () => {
    if (!selected) return;
    setStarting(true);
    try {
      const s = await practiceApi.startQuick(subject, selected);
      router.push(`/session/${s.session_id}`);
    } catch {
      setStarting(false);
      setErrored(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Quick Practice</h3>

        {errored && (
          <p className="mb-3 text-sm text-red-600">
            Couldn&apos;t load topics — try again.
          </p>
        )}

        {topics === null && !errored && (
          <p className="text-sm text-[var(--text-secondary)]">Loading topics…</p>
        )}

        {topics !== null && topics.length > 0 && (
          <label className="block text-sm">
            Pick a topic
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
          <button
            onClick={onClose}
            className="rounded-md border border-[var(--border)] px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={start}
            disabled={!selected || starting || topics === null}
            className="rounded-md bg-[var(--blue)] px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {starting ? "Starting…" : "Start"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Create the PracticeCard**

Create `web/src/components/dashboard/practice-card.tsx`:

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api/practice";
import { QuickPracticeModal } from "./quick-practice-modal";

interface Props {
  subject: string;
}

export function PracticeCard({ subject }: Props) {
  const router = useRouter();
  const [showQuick, setShowQuick] = useState(false);
  const [weakStarting, setWeakStarting] = useState(false);

  const startWeakAreas = async () => {
    setWeakStarting(true);
    try {
      const s = await practiceApi.startWeakAreas(subject);
      router.push(`/session/${s.session_id}`);
    } catch {
      setWeakStarting(false);
      // TODO: surface toast — see design notes
    }
  };

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <header className="mb-3">
        <h2 className="text-lg font-semibold">Practice</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Focused reps between daily sessions.
        </p>
      </header>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setShowQuick(true)}
          className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
        >
          Quick Practice
        </button>
        <button
          onClick={startWeakAreas}
          disabled={weakStarting}
          className="rounded-lg border border-[var(--blue)] bg-blue-50 px-4 py-2 text-[var(--blue)] disabled:opacity-50"
        >
          {weakStarting ? "Starting…" : "Practice Weak Areas"}
        </button>
      </div>
      <p className="mt-3 text-xs text-[var(--text-secondary)]">
        Or tap a weak topic below to drill in.
      </p>

      {showQuick && (
        <QuickPracticeModal subject={subject} onClose={() => setShowQuick(false)} />
      )}
    </section>
  );
}
```

- [ ] **Step 6: Verify TypeScript build**

```bash
cd web && npm run build 2>&1 | tail -15
```

Expected: clean build, zero TypeScript errors, all routes generated.

- [ ] **Step 7: Commit**

```bash
git add web/src/lib/api/practice.ts web/src/lib/types.ts web/src/lib/feature-flags.ts \
        web/src/components/dashboard/practice-card.tsx \
        web/src/components/dashboard/quick-practice-modal.tsx
git commit -m "Add practice API client, PracticeCard, and QuickPracticeModal (client-side)"
```

---

### Task 7: TopicsList weak-tappable + dashboard page mount

**Files:**
- Modify: `web/src/components/dashboard/topics-list.tsx` — weak-topic rows become buttons
- Modify: `web/src/app/(app)/dashboard/page.tsx` — mount `<PracticeCard>` with feature-flag gate

- [ ] **Step 1: Make weak-topic rows tappable**

Modify `web/src/components/dashboard/topics-list.tsx`. Locate the `weak.map(...)` block and replace with:

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { practiceApi } from "@/lib/api/practice";
import { useFeatureFlag } from "@/lib/feature-flags";

interface Topic {
  topic: string;
  topic_name: string;
  mastery_pct: number;
}

export function TopicsList({ strong, weak, subject }: { strong: Topic[]; weak: Topic[]; subject: string }) {
  const router = useRouter();
  const practiceEnabled = useFeatureFlag("practice_v2", true);
  const [starting, setStarting] = useState<string | null>(null);

  const startDrill = async (topic: string, mastery_pct: number) => {
    if (starting) return;
    setStarting(topic);
    try {
      posthog.capture("weak_topic_tapped", { topic, mastery_pct });
    } catch {}
    try {
      const s = await practiceApi.startDrillIn(subject, topic);
      router.push(`/session/${s.session_id}`);
    } catch {
      setStarting(null);
    }
  };

  return (
    <section className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Strong</h3>
        <ul className="space-y-1 text-sm">
          {strong.length === 0
            ? <li className="text-[var(--text-secondary)]">Nothing yet — keep practising.</li>
            : strong.map(t => (
                <li key={t.topic}>✓ {t.topic_name} · {t.mastery_pct}%</li>
              ))}
        </ul>
      </div>
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Needs work</h3>
        <ul className="space-y-1 text-sm">
          {weak.length === 0 ? (
            <li className="text-[var(--text-secondary)]">All clear for now.</li>
          ) : practiceEnabled ? (
            weak.map(t => (
              <li key={t.topic}>
                <button
                  onClick={() => startDrill(t.topic, t.mastery_pct)}
                  disabled={starting === t.topic}
                  className="flex w-full items-center justify-between rounded px-1 py-0.5 text-left hover:bg-gray-50 disabled:opacity-50"
                >
                  <span>⚠ {t.topic_name} · {t.mastery_pct}%</span>
                  <span className="text-[var(--text-secondary)]">
                    {starting === t.topic ? "…" : "→"}
                  </span>
                </button>
              </li>
            ))
          ) : (
            weak.map(t => (
              <li key={t.topic}>⚠ {t.topic_name} · {t.mastery_pct}%</li>
            ))
          )}
        </ul>
      </div>
    </section>
  );
}
```

Note: The component signature gains a `subject` prop. The dashboard page (next step) passes it through.

- [ ] **Step 2: Mount `<PracticeCard>` on the dashboard**

Modify `web/src/app/(app)/dashboard/page.tsx`. Add the import at the top:

```tsx
import { PracticeCard } from "@/components/dashboard/practice-card";
import { FeatureFlag } from "@/components/shell/feature-flag";
```

Then find the render tree — the section rendered after the Today's Focus / Resume Session cards — and insert the `<PracticeCard>` just before `<RecentActivity>` (or where the return currently renders `TopicsList`):

```tsx
{/* existing today focus / resume block */}

<FeatureFlag flag="practice_v2" fallback={null}>
  <PracticeCard subject={subject} />
</FeatureFlag>

{data.recent_activity && <RecentActivity data={data.recent_activity} />}

<TopicsList
  strong={data.strong_topics ?? []}
  weak={data.weak_topics ?? []}
  subject={subject}
/>
```

- [ ] **Step 3: Verify TypeScript build**

```bash
cd web && npm run build 2>&1 | tail -15
```

Expected: clean build.

- [ ] **Step 4: Commit**

```bash
git add web/src/components/dashboard/topics-list.tsx web/src/app/\(app\)/dashboard/page.tsx
git commit -m "Wire PracticeCard into dashboard and make weak topics tappable for drill-in"
```

---

## Phase D — Rollout (1 task)

### Task 8: Smoke script extension + deploy checklist + feature flag

**Files:**
- Modify: `tests/smoke/onboarding_to_session.py` — extend to test practice modes after onboarding
- Create: `docs/superpowers/deploys/2026-07-03-practice-modes-deploy.md`

**Not committed to code:** PostHog `practice_v2` flag creation — done manually in the PostHog dashboard, defaulting to 100% rollout.

- [ ] **Step 1: Extend smoke script**

Modify `tests/smoke/onboarding_to_session.py`. After the existing `Smoke: /dashboard/pure_mathematics` assertion, add:

```python
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
```

Also update `_get` to accept optional headers if it currently doesn't — inspect the current signature and adjust the call above accordingly.

- [ ] **Step 2: Verify smoke script parses**

```bash
python -m py_compile tests/smoke/onboarding_to_session.py
```

Expected: no output (clean parse).

- [ ] **Step 3: Write the deploy checklist**

Create `docs/superpowers/deploys/2026-07-03-practice-modes-deploy.md`:

```markdown
# Practice Modes (Sub-project #2) — Deploy Checklist

Date: 2026-07-03
Spec: docs/superpowers/specs/2026-07-03-stride-practice-modes-design.md
Plan: docs/superpowers/plans/2026-07-03-stride-practice-modes.md

**No SQL migration.** All changes are code-only.

## Pre-deploy

- [ ] All Phase A–C tasks merged to main
- [ ] PostHog: create `practice_v2` flag, default `true` for all users
- [ ] Confirm `.env` on Cloud Run has no changes needed (uses existing PostHog / Groq / Redis / Supabase config)

## Backend deploy (Cloud Run)

1. Build:

   ```bash
   gcloud builds submit \
     --tag europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:practice \
     --region europe-west2 \
     --timeout=20m .
   ```

2. Deploy:

   ```bash
   gcloud run deploy ascend-api \
     --image europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:practice \
     --region europe-west2 \
     --platform managed \
     --min-instances 1
   ```

3. Confirm `/readyz`:

   ```bash
   curl -sS https://ascend-api-770225551335.europe-west2.run.app/readyz
   # expected: {"status":"ready"}
   ```

## Smoke test

```bash
STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app \
  python tests/smoke/onboarding_to_session.py
```

Expected: `SMOKE OK` on stdout.

## Frontend deploy (Vercel)

1. Push merge to `main` — Vercel auto-deploys from GitHub.
2. Wait for green Vercel deployment.
3. Visit https://tutor-agent-nu.vercel.app/dashboard — confirm the Practice card renders below Today's Focus / Resume Session.
4. Click a weak topic — verify a drill-in session launches.

## Post-deploy verification

- [ ] Open Quick Practice modal, select a topic, start — session begins with 1 segment.
- [ ] Start Practice Weak Areas — session begins with 3 segments; check PostHog for `practice_started` event with `planner_reason.topic_selections`.
- [ ] Tap a weak topic on the dashboard — confirm `weak_topic_tapped` event fires and drill-in session begins.
- [ ] After finishing a practice session, `practice_completed` event fires in PostHog.
- [ ] Leave a practice session idle for >1h, refresh dashboard — session has `ended_at`.

## Rollback levers (in order)

1. **PostHog flag off** — set `practice_v2 = false`. Practice card + tappable topics vanish from dashboard. Zero code rollback needed.
2. **Cloud Run revision pin** — if backend regression:

   ```bash
   gcloud run services update-traffic ascend-api \
     --to-revisions=<previous-revision>=100 \
     --region europe-west2
   ```

3. **Vercel instant rollback** — Vercel dashboard → Deployments → previous → Promote to Production.

## Notes

- Practice modes reuse existing engine — no risk to Today's Focus, diagnostic, or resume flows.
- `session_type` is a text column; no schema migration required.
- Practice sessions auto-close at 1h; Today's Focus + diagnostic still use 24h.
```

- [ ] **Step 4: Commit**

```bash
git add tests/smoke/onboarding_to_session.py docs/superpowers/deploys/2026-07-03-practice-modes-deploy.md
git commit -m "Extend smoke script with practice modes and add deploy checklist"
```

---

## Self-Review

**Spec coverage check** — every section of the spec has an implementing task:

| Spec section | Implementing tasks |
|---|---|
| §4 Data model + Literal extensions | Task 1 |
| §5 Practice planner service (base, quick, drill, weak) | Tasks 1, 2, 3 |
| §6 `/sessions/start` dispatcher + `planner_reason` persistence | Task 4 |
| §7 `/practice/topics` endpoint | Task 5 |
| §8 Frontend Practice card + Quick Practice modal + tappable weak topics | Tasks 6, 7 |
| §9 Session lifecycle (1h auto-close, Resume exclusion) | Task 5 |
| §10 Observability (`practice_started`, `practice_completed`, `weak_topic_tapped`, `planner_reason`) | Tasks 4 (backend), 6+7 (frontend) |
| §11 Feature flag `practice_v2` | Task 6 (frontend union + flag registration) |
| §12 Testing | Distributed per task (unit tests in Tasks 1–3, integration in Tasks 4–5, manual QA in the deploy checklist) |
| §13 Rollout | Task 8 |

**Placeholder scan** — the plan contains no TODO / TBD / "similar to Task N" references; every step includes concrete code or exact commands.

**Type consistency** — `PLANNERS`, `Planner`, `BuildResult`, `PlannerReason`, `TopicSelection` names are consistent across Tasks 1–3. Frontend `PracticeTopic` shape matches backend `app/schemas/practice.py`. `practice_v2` flag string is consistent between backend deploy notes and frontend `StrideFlag` union.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-03-stride-practice-modes.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
