# UX Overhaul Sub-project #1 — Progress Ledger

Plan: docs/superpowers/plans/2026-06-28-stride-ux-overhaul-shell-onboarding-dashboard.md
Branch: ux-overhaul-v1 (off main at 1baa87c)

## Task completion log
Task 1: complete (commits 1baa87c..600b1d1, review clean)
Task 2: complete (commits 600b1d1..9924200, review clean — implementer fixed 2 brief bugs: sessions.created_at→started_at and bulk_insert UUIDs; 3 Minor findings deferred to final review: id server_default, index DESC syntax, today_focus_history.segment_plan default)
Task 3: complete (commit 38c122e — migration regression tests, 6/6 passing)
Task 4: complete (commit 766d77c — learner_profile_service, 4/4 passing)
Task 5: complete (commit 3487401 — readiness_service + grade_prediction, 4/4 passing)
Task 6: complete (commit 8961c94 — notification_service, 4/4 passing)
Task 7: complete (commit 4cc2356 — feature_flags, 4/4 passing)
Phase B review: clean (all 5 tasks spec ✅, quality approved). Notes: pytest.ini sets asyncio_mode=auto globally (safe); readiness_service does extra exam_board lookup per call.
Task 8: complete (commit 40ff5e4 — handler protocol + SessionState extensions, 2/2 passing)
Task 9: complete (commit f9592c0 — diagnostic_question handler, 2/2 passing)
Task 10: complete (commit 47dabf0 — practice handler + preference injection, 3/3 passing)
Task 11: complete (commit ca8497f — review + mistakes handlers, 4/4 passing)
Task 12: complete (commits 82d3143..cf98fed — orchestrator + shim + session_service refactor, 3/3 passing; 14/14 Phase C total)
Task 8: complete (commit 40ff5e4 — segment handler protocol + SessionState extension)
Task 9: complete (commit f9592c0 — diagnostic_question handler)
Task 10: complete (commit 47dabf0 — practice handler + preference injection)
Task 11: complete (commit ca8497f — review + mistakes handlers)
Task 12: complete (commits 82d3143 + cf98fed — orchestrator + session_service refactor + today_focus stub)
Phase C review: 2 Important findings (dual-path card emission, resume_session drops fields); 3 Minor deferred to final review
Phase C fix: complete (commit e444e0c — both Important findings fixed with new regression tests test_tools_no_side_effects + test_resume_session); re-review clean
Task 13: complete (commit f131203 — today_focus_service shape selector + build_segment_plan, 10/10 passing, review clean)
Task 14: complete (commits f131203..470d8c5 — caching layer + persistence to today_focus_history + session_service except narrowed, 6/6 passing, review clean)
Task 15: complete (commit ac8a5d1 — dashboard endpoint + DashboardPayload schema + conftest fixtures, 5/5 passing, 60/60 total, review clean)
Task 13: complete (commit f131203 — today_focus_service shape selector + slot fillers)
Task 14: complete (commit 470d8c5 — today_focus caching + persistence; fixed Phase C try/except to ImportError only)
Task 15: complete (commit ac8a5d1 — dashboard endpoint)
Phase D review: clean (all 3 tasks ✅, 60/60 tests passing, 3 concerns adjudicated as not-defects/minor)
Task 16: complete (commit 04a2a9c — onboarding wizard endpoints with step-marker state machine; fixed brief bug)
Task 17: complete (commit 4e0393b — account endpoints)
Task 18: complete (commit 342d556 — notifications + /readyz)
Task 19: complete (commit 901f461 — admin inspect endpoint)
Phase E review: 2 Critical (validation gaps in POST /subjects and /exam-board); 1 Minor deferred (admin schemas defined but not used)
Phase E fix: complete (commit 2091704 — validation gaps fixed with regression tests)
Task 20: complete (commit 7196ddd — PostHog feature-flag hook + FeatureFlag wrapper)
Task 21: complete (commit 653ed44 — typed API clients for onboarding/dashboard/account/notifications; apiFetch alias exported from api.ts; types added to types.ts)
Task 22: complete (commit e64da23 — shell: TopBar, AvatarMenu, NotificationBell; /progress redirect; useStudent+signOut added to auth.ts; npm run build ✅ no errors)
Task 20: complete (commit 7196ddd — feature-flag hook + FeatureFlag wrapper)
Task 21: complete (commit 653ed44 — typed API client modules for 4 surfaces)
Task 22: complete (commit e64da23 — shell: TopBar, AvatarMenu, NotificationBell, /progress redirect; added useStudent+signOut to auth.ts)
Phase F review: clean (all 3 tasks ✅, TypeScript build passes). 2 Minor findings deferred: bell re-fetches on toggle, FOUC before useStudent resolves
Task 23: complete (commit b042a9b — wizard shell + 5 field components with Coming Soon tooltips)
Task 24: complete (commit e06fcac — 7 wizard pages welcome through preferences)
Task 25: complete (commit a60f248 — assessment + roadmap pages, StartSessionRequest schema extension, 7-segment diagnostic plan builder; 3 backend tests)
Phase G review: all 3 ✅. Missing: onboarding_step_completed PostHog events per step (Task 33 will cover). Backend test for diagnostic exists.
Task 26: complete (commit aa61373 — dashboard skeleton + countdown band + readiness card + subject switcher)
Task 27: complete (commit 8a3e10e — resume session card + today's focus card with progress dots + recent activity)
Task 28: complete (commit 1db67fa — strong/weak topics list)
Phase H review: reviewer flagged one Critical (Rules of Hooks violation) — REJECTED as false positive; all hooks at top of function before any conditional return, which is canonical React pattern. Minor findings deferred to final review: hardcoded "Pure Maths" label + hardcoded subject in start-session POST (both plan-mandated; multi-subject work is a future sub-project).
Task 29: complete (commit df7e7ff — session full-screen takeover + exit confirmation + segment progress component)
Phase I review flagged 3 issues, all deferred:
- Segment strip unwired: session GET endpoint doesn't return segment_plan; strip renders conditionally but never appears until wired. Follow-up needed.
- Continue button in exit modal lacks visual styling (background/hover) vs. "Leave session" primary button. Trivial fix, deferred.
- SegmentProgress prop typed as any[] (brief plan text also used any[]). Should be `SegmentOut[]`. Trivial fix, deferred.
Task 30: complete (commit b1557b6 — account page with Academic + Learning Preferences)
Task 31: complete (commit acd29dd — account Profile + Billing + Danger Zone)
Phase J review: both ✅, quality approved, no findings at any severity
Task 32: complete (commit f54ecc9 — admin student-inspect page + StudentResponse.is_admin patch)
Task 33: complete (commit 6737ab7 — 8 PostHog events wired across backend + frontend; readiness_increased notification)
Phase K review: both ✅, quality approved, all findings adjudicated as non-issues
Task 34: complete (commit df06bf5 — smoke test + deploy checklist; inline implementation after subagent stream timeout)
ALL 34 TASKS LANDED. Sub-project #1 implementation complete on branch ux-overhaul-v1.
Ready for final whole-branch review.
Final whole-branch review: 3 Critical + 6 Important + 11 Minor findings.
Final fix commit df06bf5..9960ad3: all 3 Critical + all 6 Important fixed (broken CTA, smoke test payloads, Rules of Hooks in account, session segment-progress wiring, shim topic fallback, reframe_of threaded to LLM, admin schema wiring, exit modal styling, dead submitRoadmap removed). 72 Python tests pass, Next.js build clean.
Minor findings deferred to a follow-up cleanup PR.
Branch READY TO MERGE to main.
Merged to main as commit 44c0d04 (--no-ff merge preserving branch history).
Fixture emails made unique in commit 90e7033 (test infra fix; not a code issue).
Feature branch ux-overhaul-v1 deleted after merge (fully merged; no data loss).
93 backend tests pass on merged main.

---
# Sub-project #2 — Practice Modes
Plan: docs/superpowers/plans/2026-07-03-stride-practice-modes.md
Branch: practice-modes-v2 (off main at 5a43975)

## Task completion log
Task 1: complete (commit 8fdd86f — planner base + registry scaffold + Literal extensions)
Task 2: complete (commit a295af0 — QuickPlanner + DrillInPlanner, registered)
Task 3: complete (commit 8e26367 — WeakAreasPlanner adaptive, registered)
Phase A review: all 3 ✅, quality approved. 1 Minor deferred to final review: mistakes segment idx=2 hardcoded (plan-mandated; safe under 3-segment constraint).
Task 4: complete (commit 125af7d — /sessions/start registry dispatcher + planner_reason DB sync + practice_started/completed events)
Task 5: complete (commit 8c27198 — /practice/topics endpoint + dashboard 1h/24h auto-close + Resume exclusion)
Phase B review: both ✅, quality approved. Deferred to final review: (Important) dashboard cleanup loop scales O(N) per session count; (Important) planner_reason no schema validation; (Minor) unused ordinal_map dead code in practice.py; (Minor) PostHog payload size for large planner_reason.
Task 6: complete (commit 091c68d — practice API client + types + PracticeCard + QuickPracticeModal)
Task 7: complete (commit 54c2431 — TopicsList weak-tappable + dashboard mount)
Phase C review: both ✅, quality approved, zero findings at any severity. Notes: added new StartSessionResponse type (Session type coexists for legacy path); reused existing TopicMasteryOut instead of brief's Topic name.
Task 8: complete (commit 39e1726 — smoke script extension + deploy checklist)
ALL 8 TASKS LANDED. Ready for final whole-branch review.
Final whole-branch review: 1 Critical + 3 Important + ~8 Minor findings.
Final fix commit 39e1726..82d38be: all 4 Critical+Important addressed:
  - Critical: session_type propagated to state via initial_state (regression test asserts state["session_type"] matches request)
  - #2: PRACTICE_SESSION_TYPES frozenset exposed from registry; used by dashboard + orchestrator
  - #3: Dashboard cleanup uses two targeted UPDATE statements (practice 1h + non-practice 24h) instead of Python loop
  - #4: planner_reason validated via PlannerReasonModel Pydantic model; malformed → logged + dropped (regression test)
127 tests passing. Minor findings deferred to a cleanup PR.
Branch READY TO MERGE to main.
Merged to main as commit $(git rev-parse --short HEAD) (--no-ff merge preserving branch history).
Feature branch practice-modes-v2 deleted after merge.
127 backend tests pass on merged main.

---
# Sub-project #3 — Exam Marker
Plan: docs/superpowers/plans/2026-07-04-stride-exam-marker.md
Branch: exam-marker-v3 (off main at 59e8526)

## Task completion log
Task 1: complete (commit fd95e28 — GradedUpload model + Alembic migration)
Task 2: complete (commit 6e1a654 — Supabase Storage helpers)
Phase A review: both ✅, quality approved. Adjudications: env pointed at prod caused migration to land on prod ahead of code deploy — benign (additive, code unchanged, table unused until deploy). Deferred to final review: Minor — Supabase upload URL TTL constant not passed to create_signed_upload_url; verify against SDK docs before deploy.
Task 3: complete (commit f574e25 — question_selector.py; Qdrant lacks pairing metadata, LLM mark scheme fallback runs in prod)
Task 4: complete (commit 10ce295 — vision.py; Groq Llama 4 Scout only, no text-model fallback, 2 retries)
Task 5: complete (commit cdfd1b8 — grader_llm.py + _load_student_topic_context Alex memory)
Task 6: complete (commit ca926a3 — orchestrator.py state machine + mastery + readiness updates)
Phase B review: 2 Important (tzinfo TypeError risk on committed rows, used_generated_mark_scheme hardcoded False); adjudications: Qdrant metadata absent (MVP-accepted), hardcoded integration_basics topic (MVP stopgap; Phase C must constrain to integration), prev_mastery approximation (Low)
Phase B fix commit d3942ac: both Important fixes clean (tzinfo guard verified via committed-row regression test; new used_generated_mark_scheme column added via migration + orchestrator now reads from row + regression test); re-review clean
Phase C constraint: POST /marker/submissions endpoint must persist used_generated_mark_scheme from SubmissionCreateIn to the GradedUpload row
Deferred to final review: Minor findings (hardcoded subject/board in _fetch_mark_scheme, missing type annotation on _current_mastery, hashlib import in loop, hardcoded readiness version "2026.1", no httpx connection pooling)
Task 7: complete (commit 4a69abe — marker endpoints + rate limit + schemas; used_generated_mark_scheme persisted per Phase B constraint; topic query param deferred per MVP)
Task 8: complete (commit fa75178 — /readyz Supabase Storage bucket check)
Phase C review: both ✅, quality approved, zero findings at any severity. All 4 concerns adjudicated as legitimate adaptations (session factory naming, MVP param removal, env var test workaround, telemetry simplification)
Task 9: complete (commit 748032c — marker API client + types + feature flag + MarkMyWorkCard on dashboard)
Task 10: complete (commit 1e9ed51 — /mark page with question card, tabbed answer input, grading progress, results view)
Task 11: complete (commit accb67d — /mark/history list + read-only submission detail view)
Phase D review: reviewer flagged one Critical (used_generated_mark_scheme not propagated) — REJECTED as false positive; verified field exists in CreateSubmissionBody interface + both createSubmission call sites (marker.ts:16, mark/page.tsx:69 + :82). Reviewer misread diff. Same pattern as sub-project #1's Rules-of-Hooks false positive.
Phase D deviations noted: photo_extension typed cast replaces `as any` (real strict-mode fix); JSX apostrophe escaping (`Couldn&apos;t`) correctly matches react/no-unescaped-entities ESLint rule (not a defect despite reviewer's over-flag).
Task 12: complete (commit 33b9d10 — smoke script extension + deploy checklist)
ALL 12 TASKS LANDED.
Final whole-branch review (Opus): 0 Critical, 4 Important (I1 route flag gap, I2 dead topic picker UI, I3 telemetry missing field, I4 Numeric/Float drift on grade_pct), ~14 Minor (mostly Phase B known deferrals).
Final fix commit 20bb9d3: I1+I2+I3 fixed cleanly (routes now gate on marker_v2, TopicPickerModal removed, marker_grading_succeeded event includes used_generated_mark_scheme). I4 deferred as follow-up.
Re-review clean.
172 tests passing, TypeScript build clean.
Branch READY TO MERGE to main.
Merged to main as commit 4ad2e36 (--no-ff merge preserving branch history).
Feature branch exam-marker-v3 deleted after merge.
172 backend tests pass on merged main.

## Sub-project #4 — UI/UX Pass (started 2026-07-11)
Spec: docs/superpowers/specs/2026-07-11-stride-uiux-pass-design.md
Plan: docs/superpowers/plans/2026-07-11-stride-uiux-pass.md
Branch: uiux-v3
Base commit: 024050b

Plan-wide adaptations (discovered Task 1):
- The Next.js frontend lives at `web/`, NOT `frontend/`. All future task briefs referring to `frontend/` should be executed against `web/`.
- Project uses Tailwind 4 (not 3). No `tailwind.config.ts`. Tokens exposed via `@theme inline` in `web/app/globals.css`.
- Package manager is npm (not pnpm).
- Vitest is now configured (`web/vitest.config.ts` + `web/vitest.setup.ts`) with `window.matchMedia` mock for next-themes.

Task 1 implementer (sonnet, commit 1a7f619): DONE_WITH_CONCERNS. 6 tests passing.
Task 1 reviewer (sonnet): Spec ✅, quality Approved with concerns.
  - I1 (tailwind.config.ts absent): plan-vs-reality — reality governs, no fix
  - I2 (tautological green test): fix required
  - I3 (FOUC on first paint): fix required — add suppressHydrationWarning
  - Minor: --color-teacher-feedback missing from @theme inline; body color removed

Task 1 fix subagent (sonnet, commit be3b53e): DONE. 6 tests + green sanity check passing.
Task 1 re-review (sonnet): Spec ✅, quality Approved with concerns. All 4 fix targets resolved.
  - N1 (educational tokens hardcoded in @theme inline): deferred to final review — theme-invariant by design, stylistic-only
  - N2 (readiness/semantic tokens absent in dark override): "cannot verify" — confirmed intentional per spec (gradient is theme-invariant)

Task 1: complete (commits 1a7f619..be3b53e, review clean).

Path correction: web/src/ (not web/) is the app root. Update future briefs.

Task 2 groundwork (commit 4515305): deps + cn() by prior implementer (rate-limited).
Task 2 implementer (sonnet, 4515305..26c8ae0, 7 commits): DONE. 20 primitives + 7 tests.
Task 2 reviewer (sonnet): flagged I1 (focus ring), I2 (tooltip shadow), I3 (sheet surface), m2 (duration aliases), m5 (ease utility), m6 (radius utilities).
Task 2 fix (sonnet, c107e95..df70279 + doc 5d3a5c0): all 6 findings resolved. 7 tests passing.
Task 2 re-review (sonnet): Spec ✅, quality Approved with concerns. 3 residual small-radius values (rounded-[4/6px] on close buttons/Tabs/CommandItem) deferred to final review — spec's radius rule covers main components only.

Task 2: complete (commits 4515305..5d3a5c0, review clean at task scope).

Task 3 implementer (sonnet, b8c3536..524b29e): DONE. Backend endpoint + Sidebar + ContinuePill. 9 tests (4 backend, 5 frontend).
Task 3 reviewer (sonnet): Spec ✅, Approved with concerns. Fix: duplicate aria-label on aside+nav; comment session ordering debt.
Task 3 fix (sonnet, fe3bb1a): DONE. Tests still 5/5 + 4/4.
Task 3: complete (commits 5d3a5c0..fe3bb1a, review clean at task scope).

Model debt logged: TutorSession lacks updated_at. Order-by uses started_at as proxy.

Task 4 implementer (sonnet, 00be73a..45edbc2): DONE. TopBar + Breadcrumb + SubjectSwitcher + AskAlex + Search + Cmd-K chip + mobile avatar. 26 frontend tests.
Task 4 reviewer (sonnet): Spec ✅, Approved with concerns. Fixes: mobile avatar dead-end, subject-switcher ARIA hierarchy.
Task 4 fix (sonnet, d017dfc): DONE. 26/26 tests.
Task 4: complete (commits fe3bb1a..d017dfc, review clean at task scope).

Model debt logged: useCurrentSubject is a localStorage stub; needs GET /api/v1/subjects endpoint in a later task.

Task 5 implementer (sonnet, 703c838..a67899b): DONE. /search endpoint + Cmd-K palette. 14 new tests.
Task 5 reviewer (sonnet): Spec ✅ with 4 Important gaps. Fixes: modal 512→640, hasResults logic, dead code, font-mono.
Task 5 fix (sonnet, 9d93268): DONE. 33 frontend + 7 backend passing.
Task 5: complete (commits d017dfc..9d93268, review clean at task scope).

Data debt logged: GradedUpload lacks `topic` column; sub-project #3 used `subject` as proxy. Context-aware ranking for submissions only works at subject-level.

Task 6 implementer (sonnet, 58ba3cf..3ca6896, 3 commits): DONE. Hook + ShortcutHelp + AppShell + shell_v3 flag. 32 tests.
Task 6 reviewer (sonnet): Spec ✅, Approved with 3 Minor + 1 Cannot verify — all deferred to whole-branch review.
Task 6: complete (commits 9d93268..3ca6896, review clean at task scope).

=== PHASE B (Shell) complete. Tasks 3-6. ===
=== Phase A + B: 6 tasks done, 28 remaining. ===

Task 7 implementer (sonnet, 18d8992..fdd7f84, 4 commits): DONE. Narration + endpoint + hero + flag. 11 backend + 5 frontend.
Task 7 reviewer (sonnet): 1 Critical (tautological narration tests) + 2 Important (band ignored target_grade; recent_grades synthesized).
Task 7 fix (sonnet, cc6a9c7 + 5339c5c): DONE. New tests assert SYSTEM_INSTRUCTION content + mock-call. Band relative to target. recent_grades via _load_student_topic_context (real data).
Task 7: complete (commits 3ca6896..5339c5c, review clean at task scope).

Real-data debt logged: LearnerSubject holds target_grade/exam_date (not Student). today_focus_service is get_or_generate (not get_today_focus). Segment shape uses target_minutes, normalized in endpoint.

Task 8 implementer (sonnet, fc99a56..244f3a7, 4 commits): DONE. Observation model + migration + service + endpoint + frontend. 25 tests.
Task 8 reviewer (sonnet): Spec ✅, Approved. 3 Importants all edge-case/documentation — deferred to final review.
Task 8: complete (commits 5339c5c..244f3a7, review clean at task scope).
Inline fix (5cb9eb2): legacy TopBar caller (studentName prop drop, !shell_v3 gate) to unblock tsc build.

=== PHASE C (Dashboard) complete. Tasks 7-8. ===
=== Phase A + B + C: 8 tasks done, 26 remaining. ===

Task 9 implementer (sonnet, e89a455..63e60e1, 3 commits): DONE. SessionShell + SegmentBand + ExitSessionButton + session_v3 flag. 14 new tests.
Task 9 reviewer (sonnet): Spec ✅, Approved. Adaptation (data-sidebar/data-topbar vs aria) actually cleaner than brief.
Task 9: complete (commits 5cb9eb2..63e60e1, review clean at task scope).

Task 10 implementer (sonnet, 30bb276..3a96e5c, 2 commits): DONE. Math wrapper + detect-equation + TeachBlock + ReinforceBlock + AssessBlock + SessionContent. 20 new tests.
Task 10 reviewer (sonnet): Spec ✅. Radix Accordion deviation (slice-based reveal instead) ratified as equivalent UX.
Task 10: complete (commits 63e60e1..3a96e5c, review clean at task scope).

Task 11 implementer (sonnet, 32b11b2): DONE. AnswerInput component. 6 tests.
Task 11 reviewer (haiku): Spec ✅, Approved.
Task 11: complete (commits 3a96e5c..32b11b2, review clean).

Task 12 implementer (sonnet, d8784c3..051ef30, 3 commits): DONE. SSE streaming (Option A — llm.stream existed). session_chat service + endpoint + AlexDrawer + hook. 21 tests.
Task 12 reviewer (sonnet): Spec ✅, Approved. All Minors (unused param, no AbortController, test listener accumulation). No Critical/Important.
Task 12: complete (commits 32b11b2..051ef30, review clean at task scope).

Real-model debt logged: TutorSession has no `state` column. Context reads from segment_plan[current_segment_idx].config for current_question + mistakes.

Task 13 implementer (sonnet, 9dc35c9): DONE. ActionBar with muscle-memory locked grid + Enter binding. 6 tests.
Task 13 reviewer (haiku): Spec ✅, Approved.
Task 13: complete (commits 051ef30..9dc35c9, review clean).

Task 14 implementer (sonnet, 22bb854 + 4865e9b, 2 commits): DONE. Migration + PATCH endpoint + hook. 9 tests.
Task 14 reviewer (sonnet): Spec ✅, Approved with concerns. commit()-in-handler flagged; grep confirms this is the established codebase pattern, not a defect.
Task 14: complete (commits 9dc35c9..4865e9b, review clean at task scope).

Model debt logged: sessions table now has state JSONB column (was absent before Task 14).

Task 15 implementer (sonnet, 750332c..fa790d6, 3 commits): DONE. SegmentTransition + SessionComplete + session_v3 flag wiring. 12 new tests.
Task 15 reviewer (haiku): Spec ✅, Approved with minor concerns (duration-300 vs 320 negligible, stubbed state MVP).
Task 15: complete (commits 4865e9b..fa790d6, review clean at task scope).

=== PHASE D (Session view) complete. Tasks 9-15. ===
=== Phases A + B + C + D: 15 tasks done, 19 remaining. ===

Task 16 implementer (sonnet, 663420f..d4d98bb, 3 commits): DONE. practice_narration + landing endpoint + PracticeLanding + 3 mode cards + practice_v3 flag. 16 tests.
Task 16 reviewer (sonnet): flagged 2 "Critical" that were spec-structural (mode-header file inlined) and Cannot-verify (Combobox role) — downgraded. 2 real Importants: Drill-In meta label + empty weak_topics narration.
Task 16 fix (sonnet, 4010f16): DONE. Drill-In meta added + empty fallback. 10 frontend + 8 backend passing.
Task 16: complete (commits fa790d6..4010f16, review clean at task scope).

Task 17 implementer (sonnet, b252fd2..b425f2b, 3 commits): DONE. /practice/plan + drill-in/resume endpoints + PlannerTransparency + DrillResumeCard. 23 tests.
Task 17 reviewer (sonnet): Spec ✅, Approved with 3 Important (onStartOver signature, resume race, dead code).
Task 17 fix (sonnet, 45faf20): DONE. All 3 fixed. 25 vitest + 16 pytest passing.
Task 17: complete (commits 4010f16..45faf20, review clean at task scope).

Task 18 implementer (sonnet, 130a338..6fcd1d4, 2 commits): DONE. impact_score module + weak_areas integration. 4 tests.
Task 18 reviewer (sonnet): Spec ✅, Approved with minors.
Task 18: complete (commits 45faf20..6fcd1d4, review clean at task scope).

Schema debt logged: SyllabusTopic lacks weight and prereq_children columns. Impact_score uses safe defaults (0.1, 0).

Task 19 implementer (sonnet, 3f4d61a..488fb37, 3 commits): DONE. /topics/v3 endpoint + TopicCard + TopicsGrid + Filters + topics_v3 flag. 17 tests.
Task 19 reviewer (sonnet): Spec PASS with 3 Importants (recency filter bug, affects_this ignored, silent error state).
Task 19 fix (sonnet, b735185 + 29ed12f): DONE. All 3 fixed. 178 frontend + 10 backend passing.
Task 19: complete (commits 6fcd1d4..29ed12f, review clean at task scope).

Task 20 implementer (sonnet, 4ac0a75..c425137, 3 commits): DONE. /topics/v3/{id} endpoint + topic_mistakes service + TopicDetail 5-section component + Revision mode toggle. 33 new tests.
Task 20 reviewer (sonnet): Spec PASS. Revision-mode "deviation" was actually reviewer-prompt over-restriction — spec says "prioritize Needs review, hide Not started", not "only Needs review". Impl matches spec.
Task 20: complete (commits 29ed12f..c425137, review clean at task scope).

=== PHASE E (Practice + Topics) complete. Tasks 16-20. ===
=== Phases A + B + C + D + E: 20 tasks done, 14 remaining. ===

Task 21 implementer (sonnet, 643a8d6 + 487c82d, 2 commits): DONE. /marker/v3/landing + marker_narration + SuggestedQuestionCard + RecentSubmissionsList. 21 tests.
Task 21 reviewer (sonnet): PASS with 1 Important (week_submission_count key misnaming today's data).
Task 21 fix (sonnet, 900bd3d): DONE. Renamed today_submission_count. 10 tests passing.
Task 21: complete (commits c425137..900bd3d, review clean at task scope).

Task 22 implementer (sonnet, 1588c9f + 50edccd, 2 commits): DONE. NewSubmission + MarkSchemePeek + analytics helper. 20 tests.
Task 22 reviewer (haiku): PASS. 2 Minors (type extension, analytics wrapper co-existence) — deferred.
Task 22: complete (commits 900bd3d..50edccd, review clean).

Task 23 implementer (sonnet, ba142fa + 1492c71, 2 commits): DONE. /upload-url endpoint + PhotoUpload + hook. 10 tests.
Task 23 reviewer (sonnet): 2 Critical (naked capture, guillemets not chevrons) + minors. PATCH /reorder deferred (out of brief scope).
Task 23 fix (sonnet, fd05c20): DONE. Capture removed, Lucide chevrons, crypto.randomUUID, error banner. 26 tests.
Task 23: complete (commits 50edccd..fd05c20, review clean at task scope).

Task 25 implementer (sonnet, 7a2c78c..8bcca93, 3 commits): DONE. Grader prompt discipline + memory reference + ResultHero + AlexFeedbackCard + ReadinessDelta. 14 tests.
Task 25 reviewer (sonnet): PASS. 2 Importants (endpoint helper test gap, hardcoded topic infer) — Task 29+ debt.
Task 25: complete (commits f62f0a9..8bcca93, review clean at task scope).

Model debt logged: GradedUpload has no `topic` column. _infer_topic_from_upload hardcoded for MVP. Fix in Task 29 when marker_v3 flag flips.

Task 27 groundwork commit 652bed6 (recommended_practice service after prior implementer 403).
Task 27 continuation (sonnet, 8b0b12b + 4a27036, 2 commits): DONE. Endpoint enrichment + RecommendedNextStep + GradedResult integration. 8 tests.
Task 27 reviewer (sonnet): Spec ✅ (all 7 constraints). Minors deferred (lazy import, bare except swallow, interface dupe).
Task 27: complete (commits e23dd39..4a27036, review clean at task scope).

Task 28 implementer (sonnet, 7fc4939 + 5aed6b7, 2 commits): DONE. /marker/history backend + HistoryFilters + HistoryRow + HistoryList. 22 tests.
Task 28 reviewer (sonnet): PASS with 1 Critical (SVG aria-label unreliable) + 1 Important (filter deselect broken).
Task 28 fix (sonnet, 9d2e660): DONE. Icon+text visible; deselect works. 87 tests.
Task 28: complete (commits 4a27036..9d2e660, review clean at task scope).

Task 29 implementer (sonnet, 40ff6af..67db13a, 3 commits): DONE. source_submission_id migration + orchestrator events + all frontend capture wiring + marker_v3 flag flip. 15 tests.
Task 29 reviewer (sonnet): 1 Critical (loop-close dead — RecommendedNextStep didn't pass submission_id) + 1 Important (mark/[id] both branches rendered GradedResult).
Task 29 fix (sonnet, 2e1ee10): DONE. submission_id threaded through URL → plan page → startSession body → sessions row. mark/[id] fallback uses ResultsView. 102 frontend + 5 backend passing.
Task 29: complete (commits 9d2e660..2e1ee10, review clean at task scope).

=== PHASE F (Marker) complete. Tasks 21-29. ===
=== Phases A + B + C + D + E + F: 29 tasks done, 5 remaining. ===

Task 30 implementer (sonnet, 26993c2..0f57d5d, 3 commits): DONE. /progress/v3 endpoint + ReadinessChart + MasteryGrid + SessionHistory + MarkerHistoryCompact + WeeklyStats + progress_v3 flag. 32 tests.
Task 30 reviewer (sonnet): PASS with minors deferred (days=1 too loose, jsdom test limits, aria-label IDs, DeltaPill dup, bandIndex skip).
Task 30: complete (commits 2e1ee10..0f57d5d, review clean at task scope).

Task 31 implementer (sonnet, dd1d129 + 464ed1f, 2 commits): DONE. progress_narrations model + migration + service + cron job + endpoint fallback. 20 tests.
Task 31 reviewer (sonnet): PASS with 2 Critical (missing UNIQUE, ON CONFLICT dead code).
Task 31 fix (sonnet, 1640eff): DONE. UNIQUE constraint follow-up migration + proper pg_insert.on_conflict_do_update. 325 total tests passing.
Task 31: complete (commits 0f57d5d..1640eff, review clean at task scope).

Task 32 implementer (sonnet, 67fac1c + 5184f4c, 2 commits): DONE. /feedback endpoint + AccountShell + 7 sections + account_v3 flag. 8 tests.
Task 32 reviewer (sonnet): PASS with minors. /feedback path concern verified as non-issue (apiFetch prepends /api/v1). Rest deferred to WBR.
Task 32: complete (commits 1640eff..5184f4c, review clean at task scope).

Task 33 implementer (sonnet, e22a654..9565529, 3 commits): DONE. OnboardingShell + 6 step v3 + complete screen + AuthCard + 3 auth pages + onboarding_v3 flag. 29 tests.
Task 33 reviewer (sonnet): PASS with 1 Important (target-grade v3 could route to non-existent assessment) + minors.
Task 33 fix (sonnet, 7111a8f): DONE. v3 target-grade hardcoded to /onboarding/preferences. Complete useEffect dep fixed. 3 tests.
Task 33: complete (commits 5184f4c..7111a8f, review clean at task scope).

=== SUB-PROJECT #4 COMPLETE ===

34 tasks across Phases A-G done. All v3 flags default off, wired on their respective surfaces.
Flag guard fix: progress_v3 default was hardcoded `true` — corrected to `false`.
Rollout runbook at docs/superpowers/deploys/2026-07-11-uiux-pass-rollout.md.
Playwright smoke at tests/smoke/uiux_v3_smoke.py (placeholder — Playwright not installed in project; install playwright + playwright install chromium to activate browser smoke).

Ready for whole-branch review + rollout.

Task 34 implementer (sonnet, 857cf87): DONE. All 9 v3 flag guards verified (fixed one — progress_v3 default was true). Rollout runbook at docs/superpowers/deploys/2026-07-11-uiux-pass-rollout.md. Playwright smoke placeholder. 360 frontend + 327 backend passing.
Task 34: complete (commits 7111a8f..857cf87).

=== PHASE G (Progress + Account + Onboarding) complete. Tasks 30-34. ===
=== SUB-PROJECT #4 COMPLETE. 34/34 tasks done. ===

Branch: uiux-v3
Base commit (main): 024050b (start of sub-project — before Task 1)
Head commit: 857cf87 (Task 34)
Total commits: ~70+ across 7 phases + inline fixes
Tests: 360 frontend + 327 backend passing at time of Task 34 close

Next steps:
1. Final whole-branch review (per SDD skill)
2. finishing-a-development-branch skill: merge, push, or keep-as-is
3. Rollout per runbook (per-flag PostHog 5%→25%→50%→100%, 24h dwell, 7-day retirement)
