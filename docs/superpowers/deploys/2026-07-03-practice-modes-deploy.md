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
