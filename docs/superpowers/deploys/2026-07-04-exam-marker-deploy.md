# Exam Marker (Sub-project #3) — Deploy Checklist

Date: 2026-07-04
Spec: docs/superpowers/specs/2026-07-04-stride-exam-marker-design.md
Plan: docs/superpowers/plans/2026-07-04-stride-exam-marker.md

## Prerequisites (do BEFORE backend deploy)

- [ ] **Create Supabase Storage bucket `graded_uploads`** — private
- [ ] **Add RLS policy** allowing students to read their own path:
      ```sql
      CREATE POLICY "students_read_own"
        ON storage.objects FOR SELECT
        USING (bucket_id = 'graded_uploads'
               AND auth.uid()::text = split_part(name, '/', 1));
      ```
- [ ] **Add 90-day auto-delete lifecycle rule** on the bucket
- [ ] **Add Cloud Run env vars:**
  - `SUPABASE_STORAGE_BUCKET=graded_uploads`
  - `SUPABASE_URL=<existing>`
  - `SUPABASE_SERVICE_ROLE_KEY=<from Supabase project settings>`

## Backend deploy (Cloud Run)

```bash
gcloud builds submit \
  --tag europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:marker \
  --region europe-west2 \
  --timeout=20m .

gcloud run deploy ascend-api \
  --image europe-west2-docker.pkg.dev/ascend-tutor-prod/ascend-repo/ascend-api:marker \
  --region europe-west2 \
  --platform managed \
  --min-instances 1
```

Migration runs at container startup; creates `graded_uploads` table.

## Sanity checks

- [ ] `curl https://ascend-api-770225551335.europe-west2.run.app/readyz` returns `{"status":"ready"}`
- [ ] `psql $SUPABASE_URL -c "\d graded_uploads"` shows the new table with expected columns
- [ ] Supabase dashboard → Storage → confirm bucket exists, RLS attached, lifecycle configured

## Smoke test

```bash
STRIDE_API_BASE=https://ascend-api-770225551335.europe-west2.run.app \
  python tests/smoke/onboarding_to_session.py
```

Expected: `SMOKE OK` including the 4 marker probes.

## Frontend deploy (Vercel)

- Push merge commit to `main` — Vercel auto-deploys
- Wait for green Vercel deployment
- Visit https://tutor-agent-nu.vercel.app/dashboard — confirm `Mark my work` card renders
- Visit https://tutor-agent-nu.vercel.app/mark — try a typed submission end-to-end

## Post-deploy manual QA

- [ ] Type an answer → get graded → see readiness delta and exam-date anchor
- [ ] Upload a real phone photo → grades
- [ ] Illegible photo → error message, `Retake photo` button works
- [ ] Free student hits 5/month → 6th shows upgrade modal
- [ ] Visit `/mark/history` → past submissions listed → click into a past one

## Rollback levers (in order)

1. PostHog `marker_v2 = false` — Marker card + `/mark` routes disappear (`< 30s`)
2. `gcloud run services update-traffic ascend-api --to-revisions=<previous>=100 --region europe-west2`
3. Vercel instant rollback via dashboard

## Notes

- Migration is additive; safe to roll back.
- Photos auto-delete after 90 days via Supabase lifecycle rule.
- Free tier: 5 monthly submissions. Pro: unlimited.
