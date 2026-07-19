"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useFeatureFlag } from "@/lib/feature-flags";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { TopicsGrid } from "@/components/topics/topics-grid";
import { TopicsFilters, useTopicsFilters } from "@/components/topics/topics-filters";
import { topicsApi } from "@/lib/api/topics";
import type { TopicV3 } from "@/components/topics/types";
import type { StatusFilter, RecencyFilter } from "@/components/topics/topics-filters";

// ── Status filter application ─────────────────────────────────────────────────

const STATUS_MAP: Record<StatusFilter, TopicV3["status"]> = {
  mastered:     "Mastered",
  practising:   "Practising",
  needs_review: "Needs review",
  not_started:  "Not started",
};

const RECENCY_DAYS: Record<RecencyFilter, number | "never"> = {
  today:      0,
  within_7d:  7,
  within_30d: 30,
  never:      "never",
};

/**
 * Apply client-side filters to the full topics list.
 * last_practised is a relative string from the server; we do simple string matching
 * for recency rather than parsing dates (API gives human-readable strings).
 */
function applyFilters(
  topics: TopicV3[],
  statusFilters: StatusFilter[],
  recencyFilter: RecencyFilter | null
): TopicV3[] {
  let result = topics;

  if (statusFilters.length > 0) {
    const allowed = new Set(statusFilters.map((s) => STATUS_MAP[s]));
    result = result.filter((t) => allowed.has(t.status));
  }

  if (recencyFilter) {
    result = result.filter((t) => {
      const lp = t.last_practised.toLowerCase();
      if (recencyFilter === "never") return lp === "never";
      if (recencyFilter === "today") return lp === "today" || lp === "yesterday";
      if (recencyFilter === "within_7d") {
        return (
          lp === "today" ||
          lp === "yesterday" ||
          /^\d+ days? ago$/.test(lp)
        );
      }
      if (recencyFilter === "within_30d") {
        return (
          lp === "today" ||
          lp === "yesterday" ||
          /^\d+ days? ago$/.test(lp) ||
          lp === "last week" ||
          /^\d+ weeks? ago$/.test(lp)
        );
      }
      return true;
    });
  }

  return result;
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function TopicsSkeleton() {
  return (
    <div className="max-w-[1120px] mx-auto pt-12 px-6 space-y-6 animate-pulse">
      <div className="h-4 w-1/2 rounded bg-[var(--surface-2)]" />
      <div className="h-8 w-2/3 rounded bg-[var(--surface-2)]" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-[180px] rounded-card bg-[var(--surface-2)]" />
        ))}
      </div>
    </div>
  );
}

// ── Inner view — needs Suspense boundary for useSearchParams ─────────────────

function TopicsV3Inner({ subject }: { subject: string }) {
  const [topics, setTopics] = useState<TopicV3[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { filters, setStatus, setRecency, clearFilters } = useTopicsFilters();

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    topicsApi
      .getV3(subject)
      .then((data) => {
        if (!cancelled) {
          setTopics(data);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTopics([]);
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  const filtered = useMemo(
    () => applyFilters(topics ?? [], filters.status, filters.recency),
    [topics, filters.status, filters.recency]
  );

  if (isLoading || topics === null) return <TopicsSkeleton />;

  return (
    <div className="max-w-[1120px] mx-auto pt-12 px-6 space-y-6">
      <h1 className="text-[28px] font-sans text-[var(--text-primary)]">Topics</h1>

      <TopicsFilters
        filters={filters}
        onStatusChange={setStatus}
        onRecencyChange={setRecency}
        onClear={clearFilters}
      />

      <TopicsGrid topics={topics} filtered={filtered} />
    </div>
  );
}

// ── Legacy fallback ───────────────────────────────────────────────────────────

function LegacyTopicsPage() {
  return (
    <div className="max-w-[960px] mx-auto pt-12 px-4">
      <p className="text-[var(--text-secondary)]">
        Topics browser is being upgraded. Enable the <code>topics_v3</code> flag to use the new
        syllabus browser.
      </p>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function TopicsPage() {
  const v3 = useFeatureFlag("topics_v3", false);
  const { subject } = useCurrentSubject();

  if (!v3) return <LegacyTopicsPage />;

  // Suspense boundary required because TopicsV3Inner uses useSearchParams via
  // useTopicsFilters (Next.js App Router requirement).
  return (
    <Suspense fallback={<TopicsSkeleton />}>
      <TopicsV3Inner subject={subject} />
    </Suspense>
  );
}
