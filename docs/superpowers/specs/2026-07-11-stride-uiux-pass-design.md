# Stride UI/UX Pass — Design Spec

**Date:** 2026-07-11
**Sub-project:** #4 (visual + IA overhaul, all surfaces)
**Preceding work:** #1 (shell/onboarding/dashboard), #2 (practice modes), #3 (exam marker) — all shipped to production

## Overview

Redesign every student-facing surface of Stride behind per-surface v3 feature flags. The pass is not visual polish — it introduces a design token system, a Shadcn/Radix component foundation, an information-architecture rethink (dashboard consolidation, sidebar navigation, Cmd-K palette), and a per-surface Alex-narration discipline. Rollout is phased inside a single sub-project.

## Product Principles (Recap)

These four principles govern every decision in this pass. They come from `project_stride_product_principles` memory (2026-07-04):

1. **Readiness is the North Star.** Every success surface shows readiness deltas, not achievement copy.
2. **Visual brief: 50% Linear / 30% Raycast / 20% Headspace.** Precision + polish + calm warmth. Not sterile, not childish.
3. **No gamification for A-Level students.** No streaks, XP, badges, level-ups. Motivation is the exam itself.
4. **Alex has memory and personality.** Every LLM prompt receives student-history context. Never invent memories.

Two additional principles specific to this pass:

5. **Analytical, never motivational.** All product copy (not just Alex-authored strings) follows three prompt rules: never praise, never speculate, always explain *why*.
6. **One Primary button per section.** Universal button discipline for a calm UI.

## 1. Design System Foundation

### Typography

- **Geist Sans** for UI text
- **Geist Mono** for scores, percentages, marks, paper codes, question IDs (`q_abc123`), M1/A1/B1 codes, timers, keyboard shortcut chips

Type scale (px): **11 / 12 / 14 / 16 / 20 / 24 / 32 / 40**

Hierarchy:

| Size | Role |
|---|---|
| 40 | Hero (e.g. "Ready for an A?", session-complete summaries) |
| 32 | Dashboard title, topic-detail hero |
| 24 | Card title (mode cards, segment cards) |
| 20 | Section title, secondary heading |
| 16 | Body copy |
| 14 | Secondary body, form labels |
| 12 | Caption, meta |
| 11 | Metadata (Geist Mono for codes, caps for intent labels) |

Line-heights: 1.5 for body, 1.2 for display. No serif fonts anywhere.

### Color

**Primary** — warm indigo `#6268F2` (light + dark modes use the same primary, tuned per theme).

**Neutrals** (warm-tinted, never pure gray):

- Dark: `#0E0E11` (Surface 0 app bg), `#151519` (Surface 1 card), `#1C1C21` (Surface 2 elevated card / active nav), Surface 3 = dialog/drawer with soft shadow
- Light: `#FCFCFD` (Surface 0), `#F8F8FA` (Surface 1), `#FFFFFF` (Surface 2), Surface 3 white with soft shadow

**Readiness gradient (confidence scale, not progress bar):**

`Cool Blue → Indigo → Lavender → Soft Gold → Amber`

Never green. Grades aren't pass/fail; they're confidence bands. Same gradient renders everywhere readiness appears — dashboard, session-complete, marker result, progress chart, topic mastery underlines.

**Semantic colors** — muted throughout. Success/warning/danger use tinted text on a neutral background, never a bright fill. Linear pattern.

**Border color tokens:**

- Dark: `rgba(255, 255, 255, 0.06)` subtle border
- Light: `rgba(0, 0, 0, 0.08)` subtle border

**Educational semantic tokens** (domain primitives, not ad-hoc):

- `Question` (subtle left accent on question blocks)
- `Answer` (answer input focus states)
- `Hint` (revealable hint chrome)
- `MarkScheme` (M1/A1/B1 codes, formulas)
- `TeacherFeedback` (reserved for future teacher-authored content)
- `AlexFeedback` (Alex-authored improvement notes)
- `Readiness` (confidence gradient)

`AlexFeedback` explicitly not "AI Feedback" — the token names teach the codebase Alex is a character, not a chatbot.

### Spacing, Radii, Elevation

- 4px base grid
- Radii: Input 8, Button 8, Card 10, Dialog 14, Badge full-round
- Elevation: hairlines + subtle background shifts only. Shadows reserved for Dialog / Drawer / Popover / Dropdown.

### Motion

- Durations: **120ms** (hover/press), **220ms** (layout), **320ms** (page/drawer entrance). Nothing over 320ms in interactive contexts.
- Single easing token: **`cubic-bezier(.22, .61, .36, 1)`** everywhere.
- Framer Motion for controlled sequences, Tailwind transitions elsewhere.
- No parallax. No spring bounces. No celebratory motion.
- `prefers-reduced-motion` respected globally: durations → 0.

### Focus states

2px indigo ring + 2px offset. Dark theme uses a slightly brighter indigo, light theme uses a slightly darker indigo. Focus is always visible; never removed.

### Surface hierarchy

Four layers (Surface 0 → 3) formalized as tokens. Every component declares which surface it belongs to. Elevated cards (hover, drag state) shift to Surface 2 explicitly.

### Icons

Lucide, at 16 / 20 / 24 sizes.

### Component primitives (Shadcn CLI, built into repo)

Button (Primary / Secondary / Ghost / Destructive), IconButton, Input, Textarea, Card, Dialog, Sheet, Popover, Tooltip, Toast, Progress, Skeleton, Tabs, Command (Cmd-K), Badge, Separator, ToggleGroup, RadioGroup, Switch, Combobox, Accordion.

### Button philosophy

- **Primary**: filled indigo, one per section, high-visibility action
- **Secondary**: outline
- **Ghost**: text-only, most common
- **Destructive**: rare, reserved for confirm-and-delete flows

### Progress bars

Never rely on color alone. Always paired with number + label + grade:

```
82%
Ready for an A
A-
```

## 2. Navigation Shell + Cmd-K

### Sidebar (240px, collapsible to 64px icon-only, mobile: slide-in sheet)

Top:
- Stride wordmark (Geist Sans 14, letter-spacing tight)
- **Continue pill** — only when a session is in flight, persistent across browser close. Copy pattern:
  - Practice / Marker: `Integration Basics · Question 7 / 15`
  - Teach / Reinforce: `Integration Basics · 12 min remaining`
  - Chosen at render based on session-type populated field.

Primary nav (order):
1. Home (dashboard)
2. Practice
3. **Exam Marker** (not "Marker")
4. Topics
5. Progress

Bottom:
- Account (avatar + name → menu)

Alex is **not** in the sidebar. Alex lives in the top bar as a first-class action (see below).

Active nav state: Surface 2 background + 2px indigo left inset accent + indigo icon + near-white label. No filled pill. Understated Linear-style.

Keyboard: `⌘H` Home · `⌘P` Practice · `⌘M` Marker · `⌘T` Topics · `⌘G` Progress · `⌘,` Account.

### Top bar (56px desktop / 52px tablet / 48px mobile)

Left: breadcrumb, two-levels maximum. `Home` / `Practice` / `Marker` / `Progress`. Inside a session: `Practice / Integration`.

Right (in order):
- Subject switcher (Ghost dropdown, API-generic — no hardcoded "Pure Mathematics")
- **Ask Alex** button (Alex first-class action; `⌘/` opens the drawer, `⌘J` alias)
- **Search** icon (opens Cmd-K; secondary entry point beside `⌘K` chip)
- `⌘K` hint chip (Geist Mono)
- Avatar on mobile only (desktop keeps avatar in sidebar bottom — duplicate control killed)

No streaks, no notification bells, no XP.

### Cmd-K palette (Radix Command primitive)

Modal centered, 640px, Surface 3, soft shadow, 14px radius. `⌘K` from any non-session route (session rebinds `⌘K` to "Ask Alex").

Sections in order:
1. **Actions** — Start Today's Session, Open Exam Marker, Ask Alex, Start Practice
2. **Recent** — last 5 places student was (session, submission, topic)
3. **Navigate** — every nav item
4. **Topics** — every syllabus topic
5. **Account** — Toggle theme, Sign out, Settings

**Index scope**: topics, papers, submissions, exam years, formulas, glossary terms, commands. Cmd-K is the universal entry point.

**Context-aware ranking**: when the current route is scoped to a topic (Session, Marker submission, Topic detail), Integration-related items rank first, including "Ask Alex about Integration". Otherwise global fuzzy rank.

Keyboard: arrows navigate, `↵` selects, `Esc` closes. Each result shows its shortcut in Geist Mono on the right.

### Additional global shortcuts

- `/` — focus search
- `Esc` — close active drawer / dialog
- `?` — open shortcut help
- `⌘/` — Alex drawer (`⌘J` alias)
- `⌘⇧M` — start a new Marker submission (direct action, distinct from `⌘M` = go to Marker page)

### Mobile

Sidebar becomes slide-in sheet via top-left hamburger. Search icon in top bar opens Cmd-K as a bottom sheet. Alex drawer is a full-height right sheet.

## 3. Dashboard v3

### Hero

Full-width, Surface 1, single centered column max-width 960px, 48px vertical padding above the hero.

Composition, top to bottom:

**Alex narration line** — Geist Sans 16, framed by a subtle 1px left border in the Readiness-current-band color. Governed by three hard prompt rules:

1. Never praise (analytical, not motivational)
2. Never speculate (everything explainable)
3. Always explain *why* today's plan exists

Regression tests assert. Sample copies:

- *"Method selection stabilized over the last three sessions. Today moves you into mixed-topic questions where selection matters more."*
- *"Recent Integration accuracy dropped 12%. Today rebuilds the +C habit before we move on."*
- Fresh student: *"You just finished onboarding. Today's a baseline assessment across the topics you flagged strongest — 18 minutes, no marks yet."*

**Readiness snapshot** — three-line block, Geist Mono for the number:

```
Readiness
64%
Target: A
```

Gradient underline never animates. Only moves on actual readiness change. Deep-links to `/progress` on click.

**Session commitment stat** — prominent block above segment cards:

```
Today's Session
22 minutes · 3 segments
```

Answers "how long?" before commitment.

**Segment cards** — three horizontal, 32% width each, 16px gap. Cards are not individually clickable; the CTA governs the whole plan. Card body:

```
[intent · Geist Mono 11 caps]
[Topic · Geist Sans 20]

[One-sentence why · Geist Sans 14, ≤10 words]

12 min · 3 questions
```

Sample: *"Review substitution before partial fractions."* Hover brightens border to indigo, no shadow lift.

Accordion on card expand: learning objective, estimated time, skills involved. Not a lesson preview.

**Primary CTA** — one indigo button:

```
Start Today's Session
```

Only Primary button on the page. Keyboard: `↵` and `Space`. Hint chip in Geist Mono beside it.

**Evolving state** — when a session is mid-plan:

```
Resume Today's Session
Segment 2 of 3 · 14 minutes remaining
```

Same hero, adaptive CTA + line.

### Alex Observations (below the hero)

Section titled `What Alex noticed this week`. Hard cap **3 observations, never 4**. Style:

- *"Integration accuracy increased 9% after two review sessions."*
- *"Method selection stabilized on Differentiation questions."*
- *"You spend less time on setup and more on execution than two weeks ago."*

Every observation traceable server-side: `observation → SQL/query → session IDs → evidence`. Future "Why did Alex say that?" feature reads this trace. No motivational copy.

### Empty state (fresh student)

Same layout. Narration explains it. Segment cards are all Assess mode (baseline assessment). No observations block.

### Loading state

Skeleton with pulse only. No shimmer.

### Error state

If the segment planner fails:

```
Today's study plan isn't available yet. Try again in a moment.
```

Retry button. Matter-of-fact copy; no anthropomorphism.

### Rhythm

Empty space is deliberate. 32→48px vertical spacing between hero blocks, 64px around narration on large screens, min-height 180px on segment cards.

**Dashboard has no other content.** Charts, heatmaps, mastery-by-topic, history all live on the Progress page.

**Feature flag:** `dashboard_v3`.

## 4. Session View v3

### Full focus mode

During a session, hide sidebar completely (not even icon rail), no top-bar breadcrumb, no subject switcher, no account controls. Two things persist:

- Segment progress band (top)
- `Exit session` escape (top-right corner, Ghost, opens confirm-and-save dialog)

`⌘K` rebinds to "Ask Alex" during session — no global search inside session.

### Segment progress band (top, 56px)

```
Segment 2 of 3                      ≈ 7 min remaining
●━━━━━●━━━━━○
Reinforce · Integration
```

Communicates: where am I, what am I doing, what's the intent, how much longer.

Filled indigo dot with Readiness-current-band ring for current segment. Completed segments filled neutral. Upcoming hollow.

### Segment content (center, generous vertical padding)

Widths:
- Reading / explanation prose: 720–800px, 65–75 char lines
- Question content: up to 880px (always the largest visual element)

**Teach**: prose blocks (Geist Sans 16, line-height 1.6), inline KaTeX equations, Callout boxes (Surface 1, hairline, MarkScheme token color for formulas). Diagrams only when the topic requires. Ends with a single continuation button.

**Reinforce**: worked example rendered as revealable step-through (Radix Accordion, keyboard-driven). After walkthrough, one follow-up question the student attempts (same input as Assess).

**Assess**: pure question rendering (Question token left accent), max_marks chip (`[4 marks]` Geist Mono top-right), input field below.

### Answer input

Auto-growing Textarea, Geist Sans 16, switches to Geist Mono when equation patterns detected (`^` `_` `\`). Submit on `⌘↵`. Hint chip when empty: *"Show working. Alex marks method as well as answer."*

### Alex drawer

400px right-side sheet on desktop, full-height sheet on mobile. Closed by default. Triggers: `⌘/`, `⌘J` alias, top-bar Alex button, or dedicated in-session Alex icon.

**Overlays content, does not push** — content stays put. No backdrop dim (pulls focus off the work). Drawer has 1px left hairline. Scrolls independently.

Content:
- Chat history for **this session only**
- Suggested prompts based on current segment context
- Free-text input at bottom, streaming responses
- Alex knows current topic, current segment, current question, submitted work, recent mistakes in session — student never has to explain what they're looking at

`Esc` dismisses. Reopening restores exact scroll position and unsent draft.

### Bottom action bar (72px, muscle-memory locked)

Layout never shuffles:

- **Left**: `Previous` — only when a previous step is revealable (worked-example steps, review). Empty slot otherwise (not width-collapsed).
- **Center**: the one contextual primary — `Start` · `Continue` · `Check Answer` · `Reveal Hint` · `Finish Segment`. Same position, same style, only label changes.
- **Right**: `Skip` (Ghost, rare) · `More` overflow menu

Center is always the primary. Muscle memory intact.

### Autosave

Every keystroke debounces to `PATCH /sessions/:id/state` (300ms). Server persists cursor position (segment index + block index + input draft). Session hydrates from server on mount. Survives refresh, sleep, network drop, tab close.

### Segment transition interstitial

3-second minimum, `↵` continues earlier:

```
Segment Complete ✓
Reinforce finished.

Next
Assess · Differentiation
≈ 6 minutes

Continue →
```

320ms fade with the shared ease token.

### Keyboard bindings

- `Enter` — primary action outside text inputs
- `Space` — alias for Continue during read-only content
- `⌘↵` — submit answer inside Textarea
- `←` / `→` — Previous / Next inside worked-example step-through
- `⌘/` — Alex toggle (`⌘J` alias)
- `Esc` — close Alex; second `Esc` opens Exit-session confirm
- `?` — shortcut help
- `⌘K` inside session — Ask Alex

### Session-complete screen (calm)

```
Today's Session Complete

22 minutes
3 segments completed
Readiness updated to 71%

Review your progress →
```

`Review your progress →` deep-links to `/progress`. Secondary: `Back to home`. No fanfare, no emoji, no motion beyond 320ms page transition. **No animated underline** — the confidence gradient never animates anywhere in the product.

### Loading / error states

First mount: skeleton pulse for progress band + content. Transient errors: quiet inline notice + auto-retry once + manual retry button. Never send user out of session on transient error.

**Feature flag:** `session_v3`.

## 5. Exam Marker v3

### Landing (`/mark`)

- **Alex narration** — analytical, evidence-backed: *"Integration accuracy averaged 62% across the last four submissions. Today's question targets substitution before partial fractions."*
- **Suggested question card** — single primary card showing the picked question preview, `[4 marks]` chip, paper_ref in Geist Mono meta. Two actions:
  - Primary: `Submit an answer to this question`
  - Ghost: `Different Question · 2 free refreshes remaining` (Pro omits counter)
- **Recent submissions** — max 5, Geist Mono marks (`4/6`), Readiness-band delta pill, tap opens graded result view
- No histograms, no charts — those live on Progress

### New-submission flow (`/mark/new`)

Three sections on a single scrollable page (not a wizard modal):

**1. Question** — read-only at top, subtle Question token accent. Mark scheme rendered in the **reversed** default state:

```
Mark Scheme
Available after submission

You'll receive the full examiner breakdown once your attempt has been graded.

Reveal anyway
```

`Reveal anyway` opens confirm Dialog:

> "Revealing the mark scheme before answering may reduce the value of this practice session."
> Cancel · Reveal

Event `marker_mark_scheme_pre_reveal` captured for analytics. Not gating access; gating friction.

**2. Your answer** — Radix ToggleGroup with two modes:
- **Typed** — Textarea, `⌘↵` submit, mono-switch on equation patterns
- **Photo** — drag-drop zone on desktop (480×280, Surface 1, dashed hairline); mobile falls to native camera picker. Thumbnails at 96×96 with page numbers (`Page 1 · Page 2 · Page 3`) in Geist Mono. Reorder via drag. Up to 4 files. Upload direct to Supabase Storage via signed URL; backend receives metadata only.

Last-used mode persisted per student (`marker_default_input_type` column). Default renders that mode selected.

**3. Submit bar** — sticky bottom, 72px. Left: mode indicator ("Typed answer · 3 lines" or "2 photos attached"). Center: `Submit for marking` primary. Right: `Save and finish later` Ghost.

### Processing states

Four discrete phases: `Uploading → Extracting → Grading → Complete`. Copy:
- *"Uploading your photos"*
- *"Reading your handwriting"*
- *"Alex is marking your answer"*
- `4 / 6`

No percentages, no fake progress bars. Failures replace with Callout + retry button:
- Extraction: *"Couldn't read that photo clearly — please retake or try typing your answer."*
- Grading: *"Marking hasn't finished — try again in a moment."*

### Graded result view (`/mark/:id`, status = graded)

Layout, top to bottom:

**Result hero** (Surface 1, 880px column):

```
4 / 6                        (Geist Mono 40)
67%                          (Geist Sans 20, text-secondary)

Readiness                    (Geist Sans 12, text-secondary)
64 → 66                      (Geist Mono 20)
+2 · Target: A               (Geist Sans 12)
```

Mark is largest (students care about mark first). Readiness delta stacks to the right on wide screens, below on ≤768px. Internal precision: 1 decimal (`64.2 → 64.8`), display rounded to integer. Prevents "stuck at 64%" fatigue.

**Alex feedback** (Surface 1, AlexFeedback token 3px left accent):

Every feedback paragraph follows the hard prompt rule:
1. What happened
2. Why
3. What next (always ends with actionable step)

Sample: *"You dropped M1 on the substitution step. The sign flipped when you brought the constant outside — a habit worth breaking now while the algebra is simple. Try one substitution question with a negative coefficient before moving on."*

**Alex memory reference** — rendered only when `student_context.recent_grades` has ≥1 same-topic match. Prefer the most recent relevant attempt, not highest or lowest score:

*"You made the same substitution slip on your last Integration attempt (4 days ago) — this is the pattern to break."*

Never fabricated. Never rendered without evidence.

**Criteria breakdown** (Surface 1):

Radix rowset (a11y). Columns: code (Geist Mono, MarkScheme color), description (Geist Sans 14), awarded state, comment (Geist Sans 13 text-secondary).

Awarded state uses **both** an indigo Lucide check **and** the label `Awarded`. Not-awarded uses **both** an `—` glyph **and** the label `Not awarded`. Never color-only.

**Mark scheme reference** (collapsed Accordion, Surface 0):

Header: `Mark scheme`. If `used_generated_mark_scheme=True`, additional Geist Mono 11 caps tag: `Alex-generated`.

Expanding auto-scrolls to the first not-awarded criterion (targeted review), not the top.

**Recommended next step** — the Marker→Practice bridge (loop-close):

```
Recommended next step
Practice substitution with one targeted question.

[Start Practice]
```

`Start Practice` is the Primary CTA and deep-links to `/practice?mode=drill_in&topic=integration_basics&skill=substitution` — routes through the sub-project #2 planner registry.

**Actions row** — exactly two:
- Primary is `Start Practice` (moved up into the Recommended block)
- Ghost: `Try a similar question` (stays in Marker loop, re-invokes `pick_question` scoped to same topic)
- Top-left breadcrumb handles `Back to Exam Marker`. No third CTA.

No Share, no Export PDF, no Download.

### History view (`/mark/history`)

- **Filters** (top strip): topic (multi-select), status (graded / error), date range, **Difficulty** (`≤3 marks / 4–6 / 7+`). URL-persisted.
- **Row** (Radix Card, 64px):
  - Status icon (leftmost): `✓ Graded` / `⚠ Extraction failed` / `⏳ Pending` in respective semantic-muted colors
  - Date (Geist Sans 12 text-secondary)
  - Question preview (first 80 chars, single line, ellipsis) + topic tag
  - `4/6` in Geist Mono, `+2` readiness pill in gradient-current-band color
- Empty state: *"No graded submissions yet. Submit your first answer to see it here."* + Primary CTA
- Pagination: cursor-based `Show more`

### Marker v3 analytics events

- `marker_question_refreshed` (`refresh_count`, `remaining_free`)
- `marker_input_mode_selected` (`typed` / `photo`)
- `marker_mark_scheme_pre_reveal`
- `marker_ocr_failed` (`retry_attempt`)
- `marker_time_to_submit_seconds`
- `marker_time_to_grade_seconds`
- `marker_try_similar_clicked`
- `marker_recommended_practice_clicked`
- `marker_recommended_practice_completed` — the loop-close metric

**Feature flag:** `marker_v3`.

## 6. Practice + Topics v3

### Practice landing (`/practice`)

Page header (Geist Sans 32): `How do you want to practice today?` — style choice, not topic choice. The planner determines topic.

**Alex narration** — action-oriented: *"Integration Basics and Partial Fractions account for most recent lost marks. Today's practice can address either."*

**Three mode cards** frozen as the permanent mental model. No fourth mode ever. New planner logic extends an existing mode, not the nav.

Standardized card composition:

```
[intent · Geist Mono 11 caps]
[Mode name · Geist Sans 24]
[Description · Geist Sans 14]

[Meta · Geist Mono 12]

[Estimated outcome · Geist Sans 12 text-secondary]

[Estimated readiness impact]

[Start]
```

| Mode | Header line | Description | Meta | Outcome hint | Readiness impact |
|---|---|---|---|---|---|
| Quick Practice | *"I have ten minutes."* | *"A short session across recent weak areas."* | `~10 min · 5 questions` | *"Best when time is limited — keeps readiness stable."* | `Expected readiness · stable` |
| Weak Areas | *"I want to improve."* | *"Focused work on the topics slipping this week."* | `~15 min · dynamic length` | *"Best for pushing readiness up — targets highest-impact weakness."* | `Expected readiness · +2% (est.)` |
| Drill-In | *"I keep getting this wrong."* | *"Deep-focus on one topic — you choose."* | updates on topic pick | *"Best when one concept won't stick — mastery over breadth."* | `Expected mastery · +1 band on this topic` |

Language avoids promises. One CTA per card: `Start`. No Configure / Customize / More options.

### Planner transparency screen

Between clicking `Start` and the session view, show what the planner decided:

```
Today's Plan

Teach       Integration
Reinforce   Substitution
Assess      Partial Fractions

≈18 minutes · 3 segments

[Start]
[Change mode ↩]
```

Builds trust in the planner. Handles the Marker-bridge deep-link — pre-populated topic + skill shown, then confirm.

### Drill-In resumable

If an unfinished drill exists for the chosen topic:

```
Resume Drill
Partial Fractions
4/10 completed

[Resume]
[Start over]
```

Same server-side session resumption plumbing as the Continue pill.

### Weak Areas impact scoring

Ranks by composite:

```
impact_score(topic) =
    (1 − mastery)                      # weakness
  × recency_weight(last_practised)     # decayed
  × prerequisite_multiplier            # topics this unlocks
  × topic_exam_frequency               # syllabus-weighted
```

Not lowest mastery. Documented as a first-class function, unit-tested with fixtures.

### Deep-link intake

`/practice?mode=drill_in&topic=integration_basics&skill=substitution` pre-selects Drill-In, pre-fills topic, shows the planner transparency screen. Alex narration updates: *"Coming from your Exam Marker result — targeting substitution."*

### Empty state

Weak Areas disabled: *"Available after your first few questions."* Quick Practice available (syllabus-first fallback). Drill-In available.

### Topics landing (`/topics`) — syllabus browser

Not another analytics page. Job is exploration.

Header: subject switcher + analytical line: *"18 topics · 4 mastered · 6 needing revision · 8 not yet covered."* Geist Mono for numbers.

**Grid card composition** (minimal, no large progress bars):

```
Integration                        (Geist Sans 20)

Readiness         64%              (Geist Mono 20)
Last practised    2 days ago       (Geist Sans 12 text-secondary)

Needs review                       (status pill, semantic-muted)
```

Confidence-scale underline is a single 2px line under `Readiness 64%` only.

**Prerequisite link** — each card shows one *most relevant* prerequisite:

```
Chain rule fluency affects this topic →
```

Deep-links to prerequisite topic. When prerequisite mastery is low, line is Alex-authored and blunter: *"Weak chain rule is dragging this down."* Evidence-backed from mastery data; never fabricated.

**Filters** — mastery status (multi-select), last-practised recency. URL-persisted.

### Topic detail (`/topics/:topic_id`) — five fixed sections

1. **Overview** — topic name (Geist Sans 32), mastery (Geist Mono 40), syllabus reference (`Edexcel 9MA0 · Topic 4.3`), target grade context
2. **Common mistakes** — up to 3 patterns mined from student's own history. Analytical, evidence-backed: *"Across your last three attempts, substitution was correct, but limits of integration caused the lost marks."* Never generic.
3. **Recent attempts** — last 5 graded submissions on this topic, click through to Marker result view
4. **Recommended practice** — Primary CTA `Practice this topic` (deep-links Drill-In pre-loaded)
5. **Related topics** — prerequisites and downstream topics as small link cards

Order fixed. No tabs.

### Revision mode

Radix Switch in Topics header. When on: prioritize `Needs review` topics, hide `Not started`, order by planner impact score. Persists per browser session.

### Empty states — planner-positive framing

- Zero weak areas: *"No clear weak areas right now. Quick Practice will keep your readiness stable."* + Quick Practice CTA
- Fresh student: *"No practice yet. Start with Quick Practice to get baseline readings across your syllabus."* + Quick Practice CTA

Never *"No data."*

**Feature flags:** `practice_v3`, `topics_v3`.

## 7. Auth + Onboarding + Account + Progress

### Auth (`/signin`, `/signup`, `/reset`)

Single centered Surface 1 card, 400px wide, 10px radius, hairline border. Stride wordmark 20px above the card. No marketing chrome.

Sign-in:

```
Sign in

Email
Password

[Sign in]

Forgot password?  ·  New here? Create account
```

Sign-up (identical shape + Name field):

```
Create account

Name
Email
Password

[Create account]

Already have an account? Sign in
```

Fields are Radix Text inputs, 44px height, 8px radius. Password field has Ghost eye-toggle. Errors render inline in muted-danger token (never red border, never toast). Submit on `↵`. Auto-focus first field.

Post-signin → `/`. Post-signup → `/onboarding/education-system`.

**Password reset** — two screens with same card shell.

Copy is analytical: no "Welcome back!" — just "Sign in".

Auth visual shell swaps under `shell_v3`; no dedicated auth flag.

### Onboarding (`/onboarding/*`)

Six steps, same endpoints as v2. Layout revised.

**Top:** 56px band with 6 dots + connectors (same construction as segment progress).

**Center:** single centered column, max-width 560px, 96px top padding.

Each step:

```
[Analytical framing · Alex line · Geist Sans 14 text-secondary]

[Step question · Geist Sans 32]
[One-line subtitle · Geist Sans 14 text-secondary]

[Field(s)]

[Continue →]
```

Per-step framing:

- **education-system**: *"Alex needs to know your syllabus before it can plan sessions."*
- **subjects**: *"You can add more later — but a first subject lets Alex build your initial roadmap."*
- **exam-board**: *"This decides which past papers Alex uses."*
- **exam-date**: *"Alex paces your sessions against this deadline — earlier is better than optimistic."*
- **target-grade**: *"Readiness is measured against this. You can raise or lower it later."*
- **preferences**: *"Alex will lean on these when explaining new material."*

Sticky bottom bar per step: `Back` (Ghost, hidden on step 1) · `Continue` (Primary, disabled until required field valid). `↵` submits. No skip.

**Final "complete" screen:**

```
[analytical framing · "Your roadmap is ready. Alex generated a session plan for today based on your baseline."]

You're set.

Today's plan  ·  22 minutes  ·  3 segments

[Go to today's session]
```

No confetti. CTA jumps directly into today's session (fastest path to first value).

**Feature flag:** `onboarding_v3`.

### Account (`/account`) — full page

Two-pane:
- **Left rail** (240px, Surface 1, hairline right edge): section links, active state matches sidebar nav (Surface 2 + 2px indigo left inset).
- **Right pane** (max-width 720): current section content.

Sections in order: Profile · Subjects · Notifications · Theme · Keyboard Shortcuts · Feedback · Sign Out.

**Profile** — name (editable), email (read-only + Ghost "Change email"), plan (`Free` badge in Geist Mono, `Upgrade to Pro →` Ghost link inline when Free), member since. Save-on-blur; no explicit Save button.

**Subjects** — row per subject with topic count + mastery band + `Remove` Ghost. Adding opens Radix Dialog (mini exam-board flow). Removing shows confirm naming what will be deleted: *"Removing Pure Mathematics will archive 47 sessions and 12 graded submissions. Mastery data will be kept for 30 days in case you re-enable."*

**Notifications** — email settings by type (session reminders / weekly digest / marker results). Radix Switch per row. Same backend as `notifications_v2`.

**Theme** — Radix RadioGroup: Dark / Light / System. Preview swatches per option. Applies immediately.

**Keyboard Shortcuts** — grouped table, Geist Mono keys, Geist Sans descriptions. Groups: Global, Session, Marker, Alex, Cmd-K. Each key rendered as `<kbd>`. Reference doc for `?` help.

**Feedback** — Textarea + subject + Send. POSTs to `/feedback`, forwards to Resend inbox. Confirmation: *"Sent. Thanks."*

**Sign Out** — Destructive-styled button + confirm.

No upgrade modals, no dark-pattern nudges. Upgrade is Ghost link inline + `/pricing` page.

**Feature flag:** `account_v3`.

### Progress (`/progress`) — new page

Single scrollable page, max-width 1000, 48px vertical rhythm between blocks.

**Top:** Alex trend narration: *"Readiness rose from 58% to 64% over 14 days. Integration drove the gain; Partial Fractions is slipping."* Nightly refresh, cached. Same three prompt rules.

**Block 1 — Readiness over time.** 320px full-width Recharts line chart with area fill, colored by confidence gradient. `30 days` / `90 days` ToggleGroup top-right. Hover crosshair + tooltip (date, readiness %, week-delta in Geist Mono). Minimal axis labels. Empty state: skeleton + *"Your readiness graph will fill in after a few sessions."*

Compact stat row above chart (Geist Mono): current readiness / 14-day delta / target grade.

**Block 2 — Mastery by topic.** Two-column grid of mini-cards (160×80, four across on desktop). Topic name + Geist Mono mastery % + confidence-scale underline. Click → Topics detail.

**Block 3 — Session history.** Vertical list, last 20 sessions. Row: date · mode · topic(s) · duration (Geist Mono) · readiness delta pill. Click → session recap view. `Show more` (Ghost) cursor pagination.

**Block 4 — Marker history compact.** Last 10 graded, same row shape as `/mark/history`. Click through to graded result.

**Block 5 — Stats for the week.** Compact horizontal strip, Geist Mono:

```
Sessions this week   4
Questions attempted  47
Marks scored         198 / 240
Time in app          2 h 18 m
```

Data, not achievements. No trophies, no streaks, no comparison to other users.

**Loading:** top-down skeleton, pulse only.

**Empty state (zero-data):** placeholder line at target-band + *"No sessions yet. Start today's session to begin populating this graph."* CTA `Go to today's session`. Blocks 2-5 render with inline "will fill in" copy — page never looks broken.

**Feature flag:** `progress_v3` (also gates sidebar nav item's presence).

## 8. Rollout, Flags, Migration

### Feature flag inventory

| Flag | Gates | Retires |
|---|---|---|
| `shell_v3` | Sidebar, top bar, Cmd-K, tokens/primitives global | — |
| `dashboard_v3` | `/` route | `dashboard_v2` |
| `session_v3` | Session view | `session_engine_v2` |
| `practice_v3` | `/practice` + planner transparency | `practice_v2` |
| `topics_v3` | `/topics/*` | — (new IA) |
| `marker_v3` | `/mark/*` | `marker_v2` |
| `progress_v3` | `/progress` + its sidebar item | — |
| `account_v3` | `/account/*` | `account_v2` |
| `onboarding_v3` | `/onboarding/*` | `onboarding_v2` |

All flags default `false`. Read via `useFeatureFlag("<flag>", false)` — the sub-project #3 guard pattern.

Same URL routes; page components branch on flag. No `/dashboard-v3` parallel routes.

### Retirement discipline

Once a v3 flag has been at 100% for 7 days without regression signal, delete v2 code path + v2 flag in the same PR. No indefinite dual-write.

### Rollout order (single sub-project, phased tasks)

**Phase A — Foundation** (no user-visible changes)

1. Install Shadcn CLI, Radix primitives, Lucide, Recharts, Framer Motion, Geist fonts
2. Token layer (CSS variables + Tailwind theme): colors, type scale, spacing, radii, motion, borders, surfaces, educational tokens
3. Primitive components via Shadcn CLI (per Section 1 inventory)
4. Focus-ring, motion, ease tokens applied uniformly
5. Dark/light theme switch; `prefers-color-scheme` respected

**Phase B — Shell (`shell_v3`)**

Sidebar, top bar, Cmd-K, keyboard bindings, mobile sheet. Flag left off in prod; internal-user override for dogfood.

**Phase C — Dashboard (`dashboard_v3`)**

Hero, narration, segment cards, readiness snapshot, evolving CTA, observations block. Flag stays internal until Phase D lands.

**Phase D — Session (`session_v3`)** — largest phase

Focus mode, segment band, per-intent content, answer input, Alex drawer, action bar, autosave, session-complete, segment transition interstitial. Dashboard's `Start Today's Session` now routes to v3 session view.

**Phase E — Practice + Topics (`practice_v3` + `topics_v3`)** — parallel tasks

Practice landing, three mode cards, planner transparency screen, deep-link intake. Topics grid, topic detail, prerequisite links, Revision mode.

**Phase F — Marker (`marker_v3`)**

Landing, new-submission flow, processing states, graded result, Alex feedback + memory reference, mark scheme accordion, Marker→Practice bridge working end-to-end.

**Phase G — Progress + Account + Onboarding (`progress_v3` + `account_v3` + `onboarding_v3`)**

Progress page (new), Account two-pane page (7 sections), Onboarding v3 shell + narration + one-field-per-step.

**Phase H — Rollout + retire**

Gradual PostHog rollout per flag (5% → 25% → 50% → 100%). Order: shell → dashboard → session → practice → topics → marker → progress → account → onboarding. After 7 days at 100% per flag, delete v2 code + flag.

### Coexistence during rollout

- URL discipline: same URLs, flag-branched components
- Marker→Practice bridge URL (`/practice?mode=drill_in&topic=...&skill=...`) works in both v2 and v3 practice — v3 respects `skill` param, v2 falls back
- Shell/inner surface mismatch is acceptable for internal-user dogfood only; public rollout starts with shell after enough inner surfaces are v3
- No data migration; presentation-layer pass only

## 9. Testing

- **Unit tests** — every new primitive + page component, React Testing Library. 80% coverage target on new code.
- **Accessibility** — `axe-core` CI check on every new component; keyboard-navigation test per route (Tab through, no traps). Every interactive element has an accessible name.
- **Visual regression** — deferred (Playwright + Percy is a follow-up). Manual visual QA per surface per phase.
- **Smoke test extension** — `tests/smoke/onboarding_to_session.py` continues to pass (flag-agnostic). Add a light Playwright smoke walking shell + dashboard + session start under `shell_v3=true`. Catches route-level regressions.
- **Motion QA** — `prefers-reduced-motion` toggle test; durations drop to 0.
- **Dark/light QA** — every surface in both themes. WCAG AA contrast on all text.
- **Keyboard-first QA** — every screen navigable with keyboard only. Focus visible. `?` opens shortcut help from any screen.

## 10. Cross-Cutting Rules (Apply Everywhere)

- KaTeX for all math; formulas colored with the MarkScheme token
- Skeleton pulse only, never shimmer
- Empty states never say "No data" — always a planner-positive next action + CTA
- Toasts: sparse, top-right, 4s auto-dismiss, action-oriented copy
- Focus returns to trigger element on dialog/drawer close
- `prefers-reduced-motion` halves durations and disables non-essential motion
- Numbers use Geist Mono; text uses Geist Sans; never mix within a token
- One Primary button per section (universal)
- All copy is analytical, never motivational — the three Alex narration rules apply to product copy, not just Alex-authored strings

## 11. Out of Scope

- OAuth / social sign-in — auth stays email/password
- Internationalization / i18n — English only
- Right-to-left support
- Native mobile apps / PWA install prompts
- Storybook / hosted design-system doc site
- Marketing site changes
- Email/SMS template redesign
- Streaks, XP, badges, achievements (product principle: never)
- Whiteboard / native handwriting editor (photo upload covers this)
- Voice input for Alex chat
- Real-time collaboration (peer study)
- Third-party integrations (Google Classroom, LMS)
- Teacher/parent dashboards

Each could be a future sub-project; none belong here.

## 12. Success Metrics (90 days post-launch)

- Session-complete rate (v3 vs v2 baseline)
- Time-to-first-action after signin
- Marker → Practice bridge click-through rate (target ≥ 30%)
- Cmd-K activation rate
- Alex drawer activation per session
- Dark mode adoption %
- Onboarding completion rate (v3 vs v2)
- Weekly readiness delta per active user

`marker_recommended_practice_completed` is the singular loop-close metric.

## Appendix A — Anti-Goals

Documented so nothing sneaks in later:

- No fourth Practice mode ever (Quick / Weak Areas / Drill-In frozen)
- No dashboard cards below the fold — Progress owns analytics
- No animated confidence-scale underline anywhere
- No color-only status indication (accessibility)
- No motivational copy ("Great job!", "Well done", "You're crushing it")
- No student name in Alex narration ("Hi John!") — Alex talks about the work, not the person
- No confetti or celebratory motion on session/marker completion
- No parallax, no spring bounces
- No third Primary CTA on any actions row
- No dual-write of v2 + v3 code beyond the 7-day retirement window
