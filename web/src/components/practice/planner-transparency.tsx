"use client";

import { Button } from "@/components/ui/button";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";
import type { PlanSegment } from "@/lib/api/practice";

export interface PlannerTransparencyProps {
  segments: PlanSegment[];
  minutes: number;
  narration: string;
  onStart: () => void;
  onChangeMode: () => void;
}

export function PlannerTransparency({
  segments,
  minutes,
  narration,
  onStart,
  onChangeMode,
}: PlannerTransparencyProps) {
  useKeyboardShortcut("Enter", onStart, { scope: "global" });

  return (
    <div className="max-w-[640px] mx-auto pt-24 px-6 space-y-8">
      {/* Alex narration — 2px left border in readiness-2 colour */}
      <div className="text-[14px] text-white/70 border-l-2 border-[var(--readiness-2)] pl-3">
        {narration}
      </div>

      {/* Header */}
      <h1 className="text-[32px] font-sans">Today&apos;s Plan</h1>

      {/* Segments table */}
      <div className="border border-[var(--border-subtle)] rounded-[var(--radius-card)] divide-y divide-[var(--border-subtle)]">
        {segments.map((segment, i) => (
          <div key={i} className="flex justify-between px-4 py-3">
            <span className="text-[14px] font-mono uppercase tracking-wide text-white/70">
              {segment.intent}
            </span>
            <span className="text-[16px] font-sans">{segment.topic}</span>
          </div>
        ))}
      </div>

      {/* Meta: estimated time + segment count */}
      <div className="text-[12px] font-mono text-white/60">
        ≈{minutes} minutes · {segments.length} segments
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="primary" onClick={onStart}>
          Start
        </Button>
        <Button variant="ghost" onClick={onChangeMode}>
          Change mode ↩
        </Button>
      </div>
    </div>
  );
}
