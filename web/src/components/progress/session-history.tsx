"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export interface SessionHistoryItem {
  id: string;
  date: string;       // YYYY-MM-DD
  mode: string;       // "quick_practice" | "explain" | etc.
  topic?: string | null;
  duration_minutes: number;
  delta_readiness: number;
}

const MODE_LABEL: Record<string, string> = {
  quick_practice: "Quick Practice",
  explain: "Explain",
  drill: "Drill",
  weak_topics: "Weak Topics",
  practice: "Practice",
};

function formatMode(mode: string): string {
  return MODE_LABEL[mode] ?? mode.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr + "T00:00:00").toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
    });
  } catch {
    return dateStr;
  }
}

function DeltaPill({ delta }: { delta: number }) {
  if (delta === 0) return null;
  const positive = delta > 0;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium shrink-0",
        positive
          ? "bg-[var(--semantic-success-bg)] text-[var(--semantic-success-text)]"
          : "bg-[var(--semantic-danger-bg)] text-[var(--semantic-danger-text)]"
      )}
    >
      {positive ? "+" : ""}
      {delta}
    </span>
  );
}

function SessionRow({ item }: { item: SessionHistoryItem }) {
  return (
    <div
      className="flex h-14 items-center gap-3 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] px-4"
      role="listitem"
    >
      {/* Date */}
      <span className="w-[72px] shrink-0 font-sans text-[12px] text-[var(--text-secondary)]">
        {formatDate(item.date)}
      </span>

      {/* Mode */}
      <span className="w-[120px] shrink-0 font-sans text-[13px] text-[var(--text-primary)]">
        {formatMode(item.mode)}
      </span>

      {/* Topic */}
      <span className="min-w-0 flex-1 truncate font-sans text-[13px] text-[var(--text-secondary)]">
        {item.topic ? item.topic.replace(/_/g, " ") : "—"}
      </span>

      {/* Duration */}
      <span className="shrink-0 font-mono text-[12px] text-[var(--text-secondary)]">
        {item.duration_minutes > 0 ? `${item.duration_minutes}m` : "—"}
      </span>

      {/* Delta */}
      <DeltaPill delta={item.delta_readiness} />
    </div>
  );
}

interface SessionHistoryProps {
  items: SessionHistoryItem[];
  loading?: boolean;
}

const PAGE_SIZE = 10;

export function SessionHistory({ items, loading = false }: SessionHistoryProps) {
  const [limit, setLimit] = useState(PAGE_SIZE);

  if (loading) {
    return (
      <div className="space-y-2" role="list" aria-label="Session history">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-14 animate-pulse rounded-card bg-[var(--surface-1)]"
          />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="font-sans text-[14px] text-[var(--text-secondary)]">
        Your session history will appear here once you complete a session.
      </p>
    );
  }

  const visible = items.slice(0, limit);
  const hasMore = limit < items.length;

  return (
    <div className="space-y-2">
      <div className="space-y-1.5" role="list" aria-label="Session history">
        {visible.map((item) => (
          <SessionRow key={item.id} item={item} />
        ))}
      </div>
      {hasMore && (
        <button
          onClick={() => setLimit((l) => l + PAGE_SIZE)}
          className="mt-2 font-sans text-[13px] text-[var(--text-secondary)] opacity-60 hover:opacity-100 transition-opacity duration-fast"
        >
          Show more
        </button>
      )}
    </div>
  );
}
