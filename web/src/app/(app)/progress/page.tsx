"use client";

import { useCallback, useEffect, useState } from "react";
import { useFeatureFlag } from "@/lib/feature-flags";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { progressApi, type ProgressV3 } from "@/lib/api/progress";

import { ReadinessChart } from "@/components/progress/readiness-chart";
import { MasteryGrid } from "@/components/progress/mastery-grid";
import { SessionHistory } from "@/components/progress/session-history";
import { MarkerHistoryCompact } from "@/components/progress/marker-history-compact";
import { WeeklyStats } from "@/components/progress/weekly-stats";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-sans text-[16px] font-semibold text-[var(--text-primary)]">
      {children}
    </h2>
  );
}

function ProgressSkeleton() {
  return (
    <div className="space-y-8">
      <ReadinessChart series={[]} loading />
      <MasteryGrid topics={[]} loading />
    </div>
  );
}

function ProgressStub() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3">
      <p className="font-sans text-[20px] font-semibold text-[var(--text-primary)]">
        Progress coming soon
      </p>
      <p className="font-sans text-[14px] text-[var(--text-secondary)] text-center max-w-sm">
        Detailed progress tracking will be available here once the feature is enabled.
      </p>
    </div>
  );
}

export default function ProgressPage() {
  const progressEnabled = useFeatureFlag("progress_v3", false);
  const { subject } = useCurrentSubject();

  const [data, setData] = useState<ProgressV3 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState<30 | 90>(30);

  const loadData = useCallback(async () => {
    if (!subject) return;
    setLoading(true);
    setError(null);
    try {
      const result = await progressApi.getV3(subject, days);
      setData(result);
    } catch (e) {
      setError("Could not load progress data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [subject, days]);

  useEffect(() => {
    if (progressEnabled) {
      loadData();
    }
  }, [progressEnabled, loadData]);

  // ── Flag off — stub view ──────────────────────────────────────────────────
  if (!progressEnabled) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-8">
        <ProgressStub />
      </main>
    );
  }

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading && !data) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-8 space-y-8">
        <div className="space-y-1">
          <h1 className="font-sans text-[28px] font-semibold text-[var(--text-primary)]">
            Progress
          </h1>
        </div>
        <ProgressSkeleton />
      </main>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  if (error && !data) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-8">
        <div className="flex flex-col items-center justify-center gap-3 py-16">
          <p className="font-sans text-[14px] text-[var(--text-secondary)]">{error}</p>
          <button
            onClick={loadData}
            className="rounded-button bg-[var(--surface-2)] px-4 py-2 font-sans text-[14px] text-[var(--text-primary)] hover:bg-[var(--surface-1)] transition-colors duration-fast"
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  // ── Loaded ────────────────────────────────────────────────────────────────
  return (
    <main className="mx-auto max-w-4xl px-4 py-8 space-y-10">
      {/* Page header */}
      <div className="space-y-1">
        <h1 className="font-sans text-[28px] font-semibold text-[var(--text-primary)]">
          Progress
        </h1>
        {data?.narration && (
          <p className="font-sans text-[14px] text-[var(--text-secondary)] max-w-xl">
            {data.narration}
          </p>
        )}
      </div>

      {/* Weekly stats strip */}
      {data && (
        <section aria-labelledby="weekly-stats-heading">
          <SectionHeading>This week</SectionHeading>
          <div className="mt-3">
            <WeeklyStats stats={data.weekly_stats} loading={loading} />
          </div>
        </section>
      )}

      {/* Readiness chart */}
      <section aria-labelledby="readiness-chart-heading">
        <SectionHeading>Readiness over time</SectionHeading>
        <div className="mt-3">
          <ReadinessChart
            series={data?.chart_series ?? []}
            days={days}
            onDaysChange={(d) => setDays(d)}
            loading={loading}
          />
        </div>
        {/* Current + delta callout */}
        {data && !loading && (
          <div className="mt-3 flex items-center gap-3">
            <span className="font-mono text-[28px] font-semibold text-[var(--text-primary)]">
              {data.readiness_current}%
            </span>
            {data.readiness_delta_14d !== 0 && (
              <span
                className={
                  data.readiness_delta_14d > 0
                    ? "font-sans text-[14px] text-[var(--semantic-success-text)]"
                    : "font-sans text-[14px] text-[var(--semantic-danger-text)]"
                }
              >
                {data.readiness_delta_14d > 0 ? "+" : ""}
                {data.readiness_delta_14d}pp in 14 days
              </span>
            )}
          </div>
        )}
      </section>

      {/* Mastery by topic */}
      <section aria-labelledby="mastery-grid-heading">
        <SectionHeading>Mastery by topic</SectionHeading>
        <div className="mt-3">
          <MasteryGrid topics={data?.mastery_by_topic ?? []} loading={loading} />
        </div>
      </section>

      {/* Session history */}
      <section aria-labelledby="session-history-heading">
        <SectionHeading>Session history</SectionHeading>
        <div className="mt-3">
          <SessionHistory items={data?.session_history ?? []} loading={loading} />
        </div>
      </section>

      {/* Marker history compact */}
      <section aria-labelledby="marker-history-heading">
        <SectionHeading>Marked submissions</SectionHeading>
        <div className="mt-3">
          <MarkerHistoryCompact
            items={data?.marker_history_compact ?? []}
            loading={loading}
          />
        </div>
      </section>
    </main>
  );
}
