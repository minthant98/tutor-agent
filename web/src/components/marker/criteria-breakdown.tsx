"use client";

import { Check } from "lucide-react";
import type { GradingCriterion } from "@/lib/types";

interface CriteriaBreakdownProps {
  criteria: GradingCriterion[];
}

export function CriteriaBreakdown({ criteria }: CriteriaBreakdownProps) {
  return (
    <div role="table" aria-label="Criteria breakdown" className="w-full text-[14px]">
      {/* Header row */}
      <div role="row" className="grid grid-cols-[60px_1fr_120px_1fr] gap-x-4 pb-2 border-b border-[var(--border-subtle)]">
        <div role="columnheader" className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wide">
          Code
        </div>
        <div role="columnheader" className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wide">
          Description
        </div>
        <div role="columnheader" className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wide">
          Status
        </div>
        <div role="columnheader" className="text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wide">
          Comment
        </div>
      </div>

      {/* Data rows */}
      {criteria.map((criterion) => (
        <div
          key={criterion.code}
          role="row"
          aria-label={`${criterion.awarded ? "Awarded" : "Not awarded"}: ${criterion.description}`}
          className="grid grid-cols-[60px_1fr_120px_1fr] gap-x-4 py-3 border-b border-[var(--border-subtle)] last:border-0 items-start"
        >
          {/* Code column */}
          <div role="cell" className="font-mono text-[var(--color-mark-scheme)] text-[13px] pt-[1px]">
            {criterion.code}
          </div>

          {/* Description column */}
          <div role="cell" className="text-[var(--text-primary)]">
            {criterion.description}
          </div>

          {/* Status column — BOTH icon/glyph AND text label, never color-only */}
          <div role="cell" className="flex items-center gap-1.5">
            {criterion.awarded ? (
              <>
                <Check
                  className="h-4 w-4 text-indigo-500 shrink-0"
                  aria-label="Awarded"
                />
                <span className="text-[var(--text-primary)]">Awarded</span>
              </>
            ) : (
              <>
                <span className="text-[var(--text-secondary)] text-[16px] leading-none" aria-hidden="true">
                  —
                </span>
                <span className="text-[var(--text-secondary)]">Not awarded</span>
              </>
            )}
          </div>

          {/* Comment column */}
          <div role="cell" className="text-[13px] text-[var(--text-secondary)]">
            {criterion.comment || null}
          </div>
        </div>
      ))}
    </div>
  );
}
