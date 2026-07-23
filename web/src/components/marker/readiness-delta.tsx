"use client";

interface ReadinessDeltaProps {
  readinessBefore: number;
  readinessAfter: number;
  targetGrade: string;
}

/**
 * ReadinessDelta — displays the readiness change from before to after this submission.
 * Shows rounded integers (e.g. "64 → 66") with no animation.
 */
export function ReadinessDelta({
  readinessBefore,
  readinessAfter,
  targetGrade,
}: ReadinessDeltaProps) {
  const before = Math.round(readinessBefore);
  const after = Math.round(readinessAfter);
  const delta = after - before;
  const deltaStr = delta > 0 ? `+${delta}` : delta === 0 ? "±0" : `${delta}`;

  return (
    <div className="flex flex-col items-start gap-0.5">
      {/* Label */}
      <span className="font-sans text-[12px] text-[var(--text-secondary)] uppercase tracking-wide">
        Readiness
      </span>
      {/* Delta line: 64 → 66 */}
      <span
        className="font-mono text-[20px] leading-none text-[var(--text-primary)]"
        data-testid="readiness-delta-value"
      >
        {before} → {after}
      </span>
      {/* Meta: +2 · Target: A */}
      <span className="font-sans text-[12px] text-[var(--text-secondary)]">
        {deltaStr} · Target: {targetGrade}
      </span>
    </div>
  );
}
