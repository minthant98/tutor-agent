# UX Overhaul Sub-project #1 — Deploy Checklist

**Date:** 2026-06-28
**Branch:** `ux-overhaul-v1`
**Spec:** `docs/superpowers/specs/2026-06-28-stride-ux-overhaul-shell-onboarding-dashboard-design.md`
**Plan:** `docs/superpowers/plans/2026-06-28-stride-ux-overhaul-shell-onboarding-dashboard.md`

Alembic migration is additive (no DROPs). Code rollback is safe because the legacy `Student.exam_board / subjects / exam_date` columns are retained. Legacy frontend components live in `web/src/app/(app)/dashboard/_legacy.tsx` and remain reachable via the feature flag off-state.

## Pre-deploy

- [ ] All Phase A–K tasks merged to `ux-overhaul-v1`
- [ ] Merge `ux-overhaul-v1` → `main` (or open PR) once this checklist is green
- [ ] **PostHog flags created**, all defaulting to `true` (100% rollout) for authenticated users:
  - `dashboard_v2`
  - `onboarding_v2`
  - `session_engine_v2`
  - `notifications_v2`
  - `account_v2`
- [ ] Sentry alert noise threshold raised 2× for 48h (Sentry project settings)
- [ ] Verify `.env` values on Cloud Run: `GROQ_API_KEY`, `DATABASE_URL`, `SYNC_DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `POSTHOG_KEY`, `POSTHOG_HOST`, `FRONTEND_URL`, `SENTRY_DSN`
- [ ] Verify Vercel env vars: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`, `NEXT_PUBLIC_SENTRY_DSN`

## Backend deploy (Google Cloud Run)

1. Build & push image via Cloud Build (Apple Silicon can't build the ML image locally):

   ```bash
   gcloud builds submit \
     --tag europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:ux1 \
     --region europe-west2 \
     --timeout=20m .
   ```

2. Deploy to Cloud Run (europe-west2, min-instances=1 to kill cold starts):

   ```bash
   gcloud run deploy ascend-api \
     --image europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:ux1 \
     --region europe-west2 \
     --platform managed \
     --min-instances 1
   ```

3. Migration runs at container startup via `start.sh`. Watch logs:

   ```bash
   gcloud run logs read ascend-api --region europe-west2 --limit 200
   ```

4. Confirm `/readyz` returns 200:

   ```bash
   curl -sS https://ascend-api-770225551335.europe-west2.run.app/readyz | jq .
   # expected: {"status": "ready"}
   ```

## Seed verification (before swinging frontend traffic)

Connect via the Supabase session pooler:

```bash
psql "$SUPABASE_SESSION_POOLER_URL" <<'SQL'
SELECT exam_board, count(*) FROM syllabus_topics WHERE version = '2026.1' GROUP BY exam_board;
-- expected: edexcel=22, cambridge=17

SELECT count(*) FROM learner_subjects;
-- expected: >= count(students WHERE onboarding_complete = true)

-- Test write+delete against readiness_snapshots
INSERT INTO readiness_snapshots (student_id, subject, snapshot_date, readiness_pct)
    SELECT id, 'pure_mathematics', CURRENT_DATE, 0
    FROM students LIMIT 1
    ON CONFLICT DO NOTHING;
DELETE FROM readiness_snapshots WHERE readiness_pct = 0 AND snapshot_date = CURRENT_DATE;
SQL
```

## Smoke test

```bash
STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app \
    python tests/smoke/onboarding_to_session.py
# expected: "SMOKE OK" on stdout, exit 0
```

## Frontend deploy (Vercel)

1. Push the merge commit to `main` — Vercel auto-deploys from GitHub `minthant98/tutor-agent` with Root Directory = `web`.
2. Wait for green Vercel deployment.
3. Visit https://tutor-agent-nu.vercel.app — confirm the new shell + dashboard render.
4. `/progress` should 200 with a client-side redirect to `/dashboard`.

## Post-deploy verification

- [ ] Click through onboarding as a new test user; complete diagnostic
- [ ] Dashboard renders: countdown / readiness / Today's Focus / topics
- [ ] Session view is full-screen; segment-progress dots visible; close-with-progress shows the "Your progress has been saved" modal
- [ ] Account page: edit subject exam date, toggle a Learning Preference, verify save-in-place
- [ ] Notification bell shows the `diagnostic_complete` notification
- [ ] Watch Sentry for 1 hour; investigate any new error patterns
- [ ] Watch PostHog live events: confirm `onboarding_step_completed`, `onboarding_completed`, `today_focus_generated`, `segment_started`, `segment_completed`, `readiness_changed`, `notification_clicked` all fire

## Rollback levers (in order of preference)

1. **PostHog flag off per surface** (no deploy needed, <30s):
   - Toggle `dashboard_v2` / `onboarding_v2` / `session_engine_v2` / `notifications_v2` / `account_v2` to `false` in PostHog dashboard.
   - Old code paths remain in the codebase for one release.
2. **Cloud Run revision pin:**

   ```bash
   gcloud run services update-traffic ascend-api \
     --to-revisions=<previous-revision>=100 \
     --region europe-west2
   ```

3. **Vercel instant rollback** via the Vercel dashboard (Deployments → previous → Promote to Production).

Migration is additive; code rollback is safe. Old `Student.exam_board / subjects / exam_date` columns are retained for one release.

## Follow-ups (post-deploy)

- Cleanup PR after 2–4 weeks of stable production: delete legacy dashboard/onboarding components, drop retained legacy `students` columns.
- Wire the session view's segment-progress strip to real `segment_plan` from the session GET endpoint (deferred from Task 29).
- Add PostHog cohort A/B tests once we have real usage data.
- Address the accumulated Minor findings from the final whole-branch review.
