"use client";

import { cn } from "@/lib/utils";

export type SegmentState = "completed" | "current" | "upcoming";

export interface SegmentDisplay {
  intent: string;
  topic: string;
  state: SegmentState;
  minutesRemaining?: number;
  /** Optional readiness band index (0–4) for the ring color on the current dot. */
  band_color_index?: number;
}

interface SegmentBandProps {
  segments: SegmentDisplay[];
}

/**
 * SegmentBand — sticky 56px progress band shown at the top of SessionShell.
 *
 * Layout (top → bottom):
 *   Row 1: "Segment N of M" (left) · "≈ N min remaining" (right, Geist Mono 12)
 *   Row 2: dot rail (completed · current · upcoming)
 *   Row 3: current segment label — INTENT · Topic (Geist Mono 11 caps · Geist Sans)
 */
export function SegmentBand({ segments }: SegmentBandProps) {
  const currentIdx = segments.findIndex((s) => s.state === "current");
  const current = currentIdx >= 0 ? segments[currentIdx] : null;

  return (
    <div
      className={cn(
        "sticky top-0 z-10 h-14 border-b border-[var(--border-subtle)]",
        "bg-[var(--surface-0)] px-6 flex flex-col justify-center gap-1"
      )}
      aria-label="Session progress"
    >
      {/* Row 1: count + time remaining */}
      <div className="flex items-center justify-between">
        <span className="font-sans text-[14px] text-[var(--text-primary)]">
          Segment {currentIdx + 1} of {segments.length}
        </span>
        {current?.minutesRemaining != null && (
          <span className="font-mono text-[12px] text-[var(--text-muted)]">
            ≈ {current.minutesRemaining} min remaining
          </span>
        )}
      </div>

      {/* Row 2 + Row 3 merged — dots + label */}
      <div className="flex items-center gap-3">
        {/* Dot rail */}
        <ol role="list" className="flex items-center gap-1.5">
          {segments.map((seg, i) => {
            const isCurrent = seg.state === "current";
            const isCompleted = seg.state === "completed";
            const label =
              seg.state === "completed"
                ? `${seg.intent} ${seg.topic} — completed`
                : seg.state === "current"
                  ? `${seg.intent} ${seg.topic} — current`
                  : `${seg.intent} ${seg.topic} — upcoming`;

            return (
              <li
                key={i}
                role="listitem"
                aria-current={isCurrent ? "step" : undefined}
                aria-label={label}
                className={cn(
                  "w-2 h-2 rounded-full",
                  isCompleted && "bg-white/40",
                  isCurrent &&
                    "bg-[var(--primary)] ring-2 ring-[var(--readiness-2)]",
                  seg.state === "upcoming" && "border border-white/30"
                )}
              />
            );
          })}
        </ol>

        {/* Current segment label: INTENT · Topic */}
        {current && (
          <p className="text-[11px] text-[var(--text-muted)]">
            <span className="font-mono uppercase tracking-wide">
              {current.intent}
            </span>
            <span className="font-sans"> · {current.topic}</span>
          </p>
        )}
      </div>
    </div>
  );
}
