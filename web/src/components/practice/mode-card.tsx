"use client";

import { ReactNode } from "react";

export interface ModeCardProps {
  mode: "Quick Practice" | "Weak Areas" | "Drill-In";
  header: string;
  description: string;
  /** Metadata line — e.g. "~10 min · 5 questions". May be replaced by a custom slot. */
  meta?: string;
  /** Custom content to render in place of the meta line (e.g. a Combobox). */
  metaSlot?: ReactNode;
  outcome: string;
  impact: string;
  /** Extra content inserted between description and the spacer (e.g. Badge chips). */
  extraContent?: ReactNode;
  action: ReactNode;
  testId: string;
}

export function ModeCard({
  mode,
  header,
  description,
  meta,
  metaSlot,
  outcome,
  impact,
  extraContent,
  action,
  testId,
}: ModeCardProps) {
  return (
    <div
      data-testid={testId}
      className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 flex flex-col space-y-4 min-h-[280px]"
    >
      {/* Intent label */}
      <div className="text-[11px] font-mono uppercase tracking-wide text-white/60">
        {mode}
      </div>

      {/* Mode header / quote */}
      <div className="text-[24px] font-sans leading-tight">{header}</div>

      {/* Description */}
      <div className="text-[14px] text-white/70">{description}</div>

      {/* Extra content (e.g. topic chips for Weak Areas) */}
      {extraContent && <div>{extraContent}</div>}

      {/* Meta label (always shown when provided) */}
      {meta && (
        <div className="text-[12px] font-mono text-white/60">{meta}</div>
      )}

      {/* Custom meta slot (e.g. Combobox for Drill-In) */}
      {metaSlot && metaSlot}

      {/* Push footer down */}
      <div className="flex-1" />

      {/* Footer */}
      <div className="text-[12px] text-white/60">{outcome}</div>
      <div className="text-[12px] text-white/60">{impact}</div>

      {/* CTA */}
      {action}
    </div>
  );
}
