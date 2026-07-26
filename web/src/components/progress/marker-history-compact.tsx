"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

export interface MarkerHistoryItem {
  id: string;
  date: string;           // YYYY-MM-DD
  marks?: number | null;
  max_marks: number;
  delta_readiness: number;
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

function MarkerCompactRow({ item }: { item: MarkerHistoryItem }) {
  const pct =
    item.marks != null && item.max_marks > 0
      ? Math.round((item.marks / item.max_marks) * 100)
      : null;

  return (
    <Link
      href={`/mark/${item.id}`}
      className="flex h-12 items-center gap-3 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] px-4 hover:bg-[var(--surface-2)] transition-colors duration-fast"
      aria-label={`Marker submission ${item.date}${item.marks != null ? `, ${item.marks}/${item.max_marks}` : ""}`}
    >
      {/* Date */}
      <span className="w-[72px] shrink-0 font-sans text-[12px] text-[var(--text-secondary)]">
        {formatDate(item.date)}
      </span>

      {/* Score bar */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {pct !== null && (
          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-[var(--surface-2)]">
            <div
              className="h-full rounded-full"
              style={{
                width: `${pct}%`,
                background: "var(--readiness-1)",
              }}
            />
          </div>
        )}
        {/* Marks */}
        {item.marks != null ? (
          <span className="font-mono text-[13px] font-semibold text-[var(--text-primary)]">
            {item.marks}/{item.max_marks}
          </span>
        ) : (
          <span className="font-sans text-[12px] text-[var(--text-secondary)]">
            No score
          </span>
        )}
      </div>

      {/* Delta */}
      <DeltaPill delta={item.delta_readiness} />
    </Link>
  );
}

interface MarkerHistoryCompactProps {
  items: MarkerHistoryItem[];
  loading?: boolean;
}

export function MarkerHistoryCompact({ items, loading = false }: MarkerHistoryCompactProps) {
  if (loading) {
    return (
      <div className="space-y-1.5" role="list" aria-label="Marker submissions">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-12 animate-pulse rounded-card bg-[var(--surface-1)]"
          />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <p className="font-sans text-[14px] text-[var(--text-secondary)]">
        Submit a marked question to start tracking your score history here.
      </p>
    );
  }

  return (
    <div className="space-y-1.5" role="list" aria-label="Marker submissions">
      {items.map((item) => (
        <MarkerCompactRow key={item.id} item={item} />
      ))}
    </div>
  );
}
