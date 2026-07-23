"use client";
import { ReadinessDelta } from "./readiness-delta";

interface ResultHeroProps {
  marks: number;
  maxMarks: number;
  gradePct: number;
  readinessBefore: number;
  readinessAfter: number;
  targetGrade: string;
}

/**
 * ResultHero — flagship hero section for the graded result screen.
 *
 * Layout:
 * - Marks (Geist Mono 40) — largest visual element
 * - Grade % (Geist Sans 20) — secondary
 * - ReadinessDelta stacked to the right on md+ screens, below on mobile
 */
export function ResultHero({
  marks,
  maxMarks,
  gradePct,
  readinessBefore,
  readinessAfter,
  targetGrade,
}: ResultHeroProps) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      {/* Left: marks + grade % */}
      <div className="flex flex-col gap-1">
        {/* Marks — Geist Mono 40 (largest visual element) */}
        <span
          className="font-mono text-[40px] leading-none font-semibold text-[var(--text-primary)]"
          data-testid="result-marks"
        >
          {marks} / {maxMarks}
        </span>
        {/* Grade % — Geist Sans 20 secondary */}
        <span
          className="font-sans text-[20px] text-[var(--text-secondary)]"
          data-testid="result-grade-pct"
        >
          {Math.round(gradePct)}%
        </span>
      </div>

      {/* Right: readiness delta */}
      <ReadinessDelta
        readinessBefore={readinessBefore}
        readinessAfter={readinessAfter}
        targetGrade={targetGrade}
      />
    </div>
  );
}
