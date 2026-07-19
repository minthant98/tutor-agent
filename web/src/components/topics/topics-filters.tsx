"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback } from "react";

// Status filter options
export const STATUS_OPTIONS = [
  { value: "mastered",     label: "Mastered" },
  { value: "practising",   label: "Practising" },
  { value: "needs_review", label: "Needs review" },
  { value: "not_started",  label: "Not started" },
] as const;

// Recency filter options
export const RECENCY_OPTIONS = [
  { value: "today",      label: "Today" },
  { value: "within_7d",  label: "Within 7 days" },
  { value: "within_30d", label: "Within 30 days" },
  { value: "never",      label: "Never" },
] as const;

export type StatusFilter = typeof STATUS_OPTIONS[number]["value"];
export type RecencyFilter = typeof RECENCY_OPTIONS[number]["value"];

export interface FiltersState {
  status: StatusFilter[];
  recency: RecencyFilter | null;
}

/** Read filters from URL search params. */
export function useTopicsFilters(): {
  filters: FiltersState;
  setStatus: (values: StatusFilter[]) => void;
  setRecency: (value: RecencyFilter | null) => void;
  clearFilters: () => void;
} {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const filters: FiltersState = {
    status: (searchParams.getAll("status") as StatusFilter[]).filter(Boolean),
    recency: (searchParams.get("recency") as RecencyFilter | null) ?? null,
  };

  const updateParams = useCallback(
    (newFilters: Partial<FiltersState>) => {
      const params = new URLSearchParams(searchParams.toString());

      if (newFilters.status !== undefined) {
        params.delete("status");
        newFilters.status.forEach((v) => params.append("status", v));
      }
      if ("recency" in newFilters) {
        if (newFilters.recency) {
          params.set("recency", newFilters.recency);
        } else {
          params.delete("recency");
        }
      }

      const qs = params.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [searchParams, router, pathname]
  );

  return {
    filters,
    setStatus: (values) => updateParams({ status: values }),
    setRecency: (value) => updateParams({ recency: value }),
    clearFilters: () => updateParams({ status: [], recency: null }),
  };
}

interface TopicsFiltersProps {
  filters: FiltersState;
  onStatusChange: (values: StatusFilter[]) => void;
  onRecencyChange: (value: RecencyFilter | null) => void;
  onClear: () => void;
}

export function TopicsFilters({
  filters,
  onStatusChange,
  onRecencyChange,
  onClear,
}: TopicsFiltersProps) {
  const hasActiveFilters = filters.status.length > 0 || filters.recency !== null;

  function toggleStatus(value: StatusFilter) {
    const next = filters.status.includes(value)
      ? filters.status.filter((v) => v !== value)
      : [...filters.status, value];
    onStatusChange(next);
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Status multi-select */}
      <div className="flex flex-wrap gap-2">
        <span className="text-[12px] text-[var(--text-secondary)] self-center">Status:</span>
        {STATUS_OPTIONS.map((opt) => {
          const active = filters.status.includes(opt.value);
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggleStatus(opt.value)}
              className={`px-3 py-1 rounded-full text-[12px] border transition-colors duration-fast ${
                active
                  ? "bg-[var(--primary)] text-white border-[var(--primary)]"
                  : "bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
              }`}
              aria-pressed={active}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Recency select */}
      <div className="flex items-center gap-2">
        <span className="text-[12px] text-[var(--text-secondary)]">Practised:</span>
        <select
          value={filters.recency ?? ""}
          onChange={(e) =>
            onRecencyChange((e.target.value as RecencyFilter) || null)
          }
          className="text-[12px] bg-[var(--surface-1)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-default)]"
        >
          <option value="">Any time</option>
          {RECENCY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Clear filters */}
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClear}
          className="text-[12px] text-[var(--text-secondary)] underline hover:text-[var(--text-primary)]"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
