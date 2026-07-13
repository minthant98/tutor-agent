interface ReadinessSnapshotData {
  percent: number;
  band: string;
  target_grade: string;
  days_to_exam: number | null;
}

interface ReadinessSnapshotProps {
  snapshot: ReadinessSnapshotData;
}

export function ReadinessSnapshot({ snapshot }: ReadinessSnapshotProps) {
  return (
    <div className="flex flex-col items-start gap-1">
      <span className="font-sans text-[12px] text-[var(--text-secondary)] uppercase tracking-wide">
        Readiness
      </span>
      <span className="font-mono text-[40px] leading-none text-[var(--text-primary)]">
        {snapshot.percent}%
      </span>
      <span className="font-sans text-[12px] text-[var(--text-secondary)]">
        Target: {snapshot.target_grade}
      </span>
    </div>
  );
}
