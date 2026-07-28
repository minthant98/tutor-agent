# UI/UX Pass Rollout

## Prerequisites
- All v3 flags exist in PostHog, default off
- Playwright smoke suite passes in CI against staging with shell_v3=on
- Manual visual QA per surface complete in both themes
- Accessibility (axe-core) CI green for all new components
- Screenshot review approved in both Dark and Light modes

## Rollout Order (per-flag, 24h dwell between stages)

1. shell_v3 (only after Phases C-G are internally validated)
2. dashboard_v3
3. session_v3
4. practice_v3 + topics_v3 (parallel — flip together)
5. marker_v3
6. progress_v3
7. account_v3
8. onboarding_v3 (last — safest, affects new users only)

Stages per flag: 5% → 25% → 50% → 100%.

## Metrics to watch

- Error rate per surface (Sentry)
- Session-complete rate (analytics)
- Marker→Practice bridge CTR (target ≥ 30%)
- Support/feedback inbox

## Retirement (per-flag, +7 days at 100%)

Delete v2 code path + v2 flag in the same PR. Merge after regression suite green.

## Rollback (per-flag)

Flip flag back to previous stage. No hotfix commit required — flag-gated code paths retain both implementations until retirement.

## Success metrics review (T+90 days)

See spec Section 12 for the singular loop-close metric: `marker_recommended_practice_completed`.
