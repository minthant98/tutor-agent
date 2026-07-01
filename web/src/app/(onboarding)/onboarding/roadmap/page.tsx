"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { dashboardApi } from "@/lib/api/dashboard";
import { onboardingApi } from "@/lib/api/onboarding";
import type { DashboardPayload } from "@/lib/types";

export default function RoadmapStep() {
  const router = useRouter();
  const startTime = useRef<number>(Date.now());
  const [data, setData] = useState<DashboardPayload | null>(null);

  useEffect(() => {
    startTime.current = Date.now();
    dashboardApi.get("pure_mathematics").then(setData).catch(() => setData(null));
  }, []);

  if (!data) {
    return (
      <WizardShell step="roadmap">
        <p className="text-[var(--text-secondary)]">Building your roadmap…</p>
      </WizardShell>
    );
  }

  return (
    <WizardShell step="roadmap">
      <h1 className="mb-2 text-2xl font-semibold">
        Your exam roadmap is ready.
      </h1>
      <dl className="my-6 grid grid-cols-2 gap-4">
        <div>
          <dt className="text-sm text-[var(--text-secondary)]">Readiness</dt>
          <dd className="text-2xl font-semibold">
            {Math.round(data.readiness_pct)}%
          </dd>
        </div>
        <div>
          <dt className="text-sm text-[var(--text-secondary)]">Target</dt>
          <dd className="text-2xl font-semibold">{data.target_grade}</dd>
        </div>
        <div>
          <dt className="text-sm text-[var(--text-secondary)]">Days remaining</dt>
          <dd className="text-2xl font-semibold">
            {data.days_until_exam ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-[var(--text-secondary)]">
            Recommended study
          </dt>
          <dd className="text-2xl font-semibold">25 min/day</dd>
        </div>
      </dl>
      {data.weak_topics?.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">
            Priority topics
          </h2>
          <ul className="grid gap-1 text-sm">
            {data.weak_topics.slice(0, 3).map((t, i) => (
              <li key={t.topic}>
                {i + 1}. {t.topic_name}
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        onClick={async () => {
          await onboardingApi.finalize();
          try {
            posthog.capture("onboarding_completed", {
              subjects: data?.subject ? [data.subject] : [],
              board: data?.today_focus ? undefined : undefined,
              time_to_complete_sec: Math.round((Date.now() - startTime.current) / 1000),
            });
          } catch (_) {}
          router.push("/dashboard");
        }}
        className="rounded-lg bg-[var(--blue)] px-5 py-3 text-white"
      >
        Start your first session
      </button>
    </WizardShell>
  );
}
