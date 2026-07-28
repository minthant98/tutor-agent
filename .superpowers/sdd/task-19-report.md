# Task 19 Report — Topics landing (syllabus browser)

**Status:** DONE

## Commits

- **Commit A** `3f4d61a` — Backend: `GET /api/v1/topics/v3` endpoint + `test_topics_v3_endpoint.py`
- **Commit B** `465d08d` — Frontend: `TopicCard`, `TopicsGrid`, `PrerequisiteLink`, `types.ts`, `topic-card.test.tsx`
- **Commit C** `488fb37` — Frontend: `TopicsFilters`, `topics/page.tsx` (v3 branch), `topicsApi`, `topics_v3` feature flag

## Test summary

- Backend: **10/10 passed** — list, auth required, 404, fresh-student all-Not-started, status band thresholds (Mastered/Practising/Needs review), relative last_practised, prerequisite always null, ordinal ordering
- Frontend: **157/157 passed** (all pre-existing + 7 new `topic-card.test.tsx`) — four-field render, no progressbar, prerequisite link, Alex note variant, Mastered badge, Never last_practised, navigable link role

## Key decisions

- **Prerequisite:** always `null` (MVP safe path — `SyllabusTopic` model has no prereq graph).
- **Nested `<a>` fix:** `TopicCard` uses `div[role=link]` + `useRouter().push` instead of `<Link>` to avoid HTML validity error when a `PrerequisiteLink` `<a>` is nested inside.
- **Client-side filter logic:** recency filtering does string matching against the relative strings returned by the API (e.g. "today", "3 days ago") — avoids re-fetch and is sufficient for MVP.
- **Suspense boundary:** `topics/page.tsx` wraps the inner view in `<Suspense>` because `useTopicsFilters` calls `useSearchParams()` which requires it in Next.js App Router.

## Concerns

- None blocking. The recency filter string-matching is a heuristic; if the API ever returns ISO dates instead of relative strings, the filter will break and would need updating.

---

## Fix note — review findings (post-commit 488fb37)

**Commit:** see below

Three review findings fixed:

### Fix 1 — Recency filter bounds
The `within_7d` / `within_30d` regex `/^\d+ days? ago$/` matched any number
(e.g. "20 days ago" incorrectly matched `within_7d`). Replaced with
`isWithinDays(last, maxDays)` helper that parses the integer and enforces
numeric bounds. Both `isWithinDays` and `applyFilters` are now exported for
direct unit testing. New tests cover boundary cases: 7 days (inclusive),
8 days (excluded), 20 days vs 7-day vs 30-day filter.

### Fix 2 — `affects_this` guard in PrerequisiteLink
`PrerequisiteLink` previously rendered unconditionally. Added early-return
`if (!prerequisite.affects_this) return null` at the top of the component.
`TopicCard` updated to also short-circuit via `topic.prerequisite.affects_this`
on the caller side. New test asserts nothing renders when `affects_this: false`.

### Fix 3 — Silent error state
`TopicsV3Inner` previously swallowed fetch errors by setting `topics = []`,
making errors indistinguishable from an empty syllabus. Added `error` state
(`useState<Error | null>`). On catch, `error` is set; the component renders a
callout "Something went wrong loading topics. Try again in a moment." with a
Retry button that re-fires `fetchTopics`. The empty state ("No topics for this
subject yet.") is only reachable on a successful fetch returning zero topics.
Three new tests: error callout renders on failure, absent on success, Retry
re-fires fetch.

**Test results after fix:** 178 frontend (vitest) + 10 backend (pytest) — all passed.
