"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { onboardingApi } from "@/lib/api/onboarding";
import { OnboardingComplete } from "@/components/onboarding/onboarding-complete";

interface PlanMeta {
  minutes: number;
  segments: number;
  sessionHref?: string;
}

/**
 * /onboarding/complete — v3 exit surface.
 *
 * Finalizes the onboarding wizard on mount, then renders the OnboardingComplete
 * component. If session data cannot be loaded, falls back to a sensible default
 * plan so the user can still proceed.
 */
export default function OnboardingCompletePage() {
  const router = useRouter();
  const [plan, setPlan] = useState<PlanMeta>({ minutes: 22, segments: 3 });

  useEffect(() => {
    (async () => {
      try {
        // Finalize is idempotent — safe to call if wizard already completed.
        await onboardingApi.finalize();
      } catch {
        // Not fatal — proceed to dashboard.
      }

      // Attempt to get a session ID to deep-link into.
      try {
        const { apiFetch } = await import("@/lib/api");
        const session = await apiFetch<{ session_id: string; total_minutes?: number; segments?: unknown[] }>(
          "/sessions/start",
          {
            method: "POST",
            body: JSON.stringify({}),
          }
        );
        setPlan({
          minutes: session.total_minutes ?? 22,
          segments: Array.isArray(session.segments) ? session.segments.length : 3,
          sessionHref: session.session_id
            ? `/session/${session.session_id}`
            : "/sessions/today",
        });
      } catch {
        // If session endpoint fails, fall back to /sessions/today.
        setPlan({ minutes: 22, segments: 3, sessionHref: "/sessions/today" });
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <OnboardingComplete plan={plan} />;
}
