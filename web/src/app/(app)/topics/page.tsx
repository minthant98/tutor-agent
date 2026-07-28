"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useFeatureFlag } from "@/lib/feature-flags";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { TopicsGrid } from "@/components/topics/topics-grid";
import { TopicsFilters, useTopicsFilters } from "@/components/topics/topics-filters";
import {
  RevisionModeToggle,
  readRevisionMode,
  writeRevisionMode,
} from "@/components/topics/revision-mode-toggle";
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

/**
 * Return true when the relative last_practised string falls within maxDays.
 * Parses numeric bounds to avoid false positives (e.g. "20 days ago" must NOT
 * match within_7d).
 */
export function isWithinDays(last: string, maxDays: number): boolean {
  const lp = last.toLowerCase();
  if (lp === "today" || lp === "yesterday") return true;
  const m = lp.match(/^(\d+) days? ago$/);
  if (m) return parseInt(m[1], 10) <= maxDays;
  // "N weeks ago" — convert to days
  const w = lp.match(/^(\d+) weeks? ago$/);
  if (w) return parseInt(w[1], 10) * 7 <= maxDays;
  if (lp === "last week") return 7 <= maxDays;  // "last week" ≈ 7 days
  return false;  // "Never" or anything else — excluded
}

/**
 * Apply client-side filters to the full topics list.
 * last_practised is a relative string from the server; we parse numeric bounds
 * for recency to enforce correct day thresholds.
 */
export function applyFilters(
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
      const lp = t.last_practised;
      if (recencyFilter === "never") return lp === "Never";
      if (recencyFilter === "today") {
        const lower = lp.toLowerCase();
        return lower === "today" || lower === "yesterday";
      }
      if (recencyFilter === "within_7d") return isWithinDays(lp, 7);
      if (recencyFilter === "within_30d") return isWithinDays(lp, 30);
      return true;
    });
  }

  return result;
}

// ── Revision mode filter + sort ───────────────────────────────────────────────

/**
 * When Revision mode is on:
 *   - Hide "Not started" topics
 *   - Show only "Needs review", "Practising", "Mastered"
 *   - Sort by mastery ascending (lowest mastery = highest revision priority)
 */
export function applyRevisionMode(topics: TopicV3[]): TopicV3[] {
  const NEEDS_REVISION: TopicV3["status"][] = ["Needs review", "Practising", "Mastered"];
  return [...topics]
    .filter((t) => NEEDS_REVISION.includes(t.status))
    .sort((a, b) => a.mastery - b.mastery);
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

export function TopicsV3Inner({ subject }: { subject: string }) {
  const [topics, setTopics] = useState<TopicV3[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { filters, setStatus, setRecency, clearFilters } = useTopicsFilters();

  // Revision mode — persisted to sessionStorage
  const [revisionMode, setRevisionMode] = useState(false);

  // Initialise from sessionStorage after mount (client-only)
  useEffect(() => {
    setRevisionMode(readRevisionMode());
  }, []);

  const handleRevisionModeChange = (v: boolean) => {
    setRevisionMode(v);
    writeRevisionMode(v);
  };

  const fetchTopics = useCallback(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    topicsApi
      .getV3(subject)
      .then((data) => {
        if (!cancelled) {
          setTopics(data);
          setIsLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error("Failed to load topics"));
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  useEffect(() => {
    return fetchTopics();
  }, [fetchTopics]);

  const filtered = useMemo(() => {
    // Revision mode takes precedence over individual status/recency filters
    if (revisionMode) {
      return applyRevisionMode(topics ?? []);
    }
    return applyFilters(topics ?? [], filters.status, filters.recency);
  }, [topics, filters.status, filters.recency, revisionMode]);

  if (isLoading || (topics === null && error === null)) return <TopicsSkeleton />;

  if (error) {
    return (
      <div className="max-w-[1120px] mx-auto pt-12 px-6">
        <div className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 space-y-3">
          <p className="text-[var(--text-primary)]">
            Something went wrong loading topics. Try again in a moment.
          </p>
          <button
            type="button"
            onClick={fetchTopics}
            className="text-[14px] text-[var(--accent)] hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1120px] mx-auto pt-12 px-6 space-y-6">
      {/* Header row: title + revision mode toggle */}
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-[28px] font-sans text-[var(--text-primary)]">Topics</h1>
        <RevisionModeToggle value={revisionMode} onChange={handleRevisionModeChange} />
      </div>

      {/* Filters — hidden when revision mode is on (revision mode replaces filters) */}
      {!revisionMode && (
        <TopicsFilters
          filters={filters}
          onStatusChange={setStatus}
          onRecencyChange={setRecency}
          onClear={clearFilters}
        />
      )}

      <TopicsGrid topics={topics ?? []} filtered={filtered} />
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
