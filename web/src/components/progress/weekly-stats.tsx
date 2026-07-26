"use client";

import { Skeleton } from "@/components/ui/skeleton";

export interface WeeklyStatsData {
  sessions_this_week: number;
  questions_attempted: number;
  marks_scored: number;
  marks_max: number;
  time_in_app_minutes: number;
}

interface StatCellProps {
  value: string;
  label: string;
  sub?: string;
}

function StatCell({ value, label, sub }: StatCellProps) {
  return (
    <div className="flex flex-1 flex-col items-center gap-1 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] py-4 px-2 text-center">
      <span className="font-mono text-[28px] font-semibold leading-none text-[var(--text-primary)]">
        {value}
      </span>
      {sub && (
        <span className="font-sans text-[11px] text-[var(--text-secondary)]">{sub}</span>
      )}
      <span className="font-sans text-[12px] text-[var(--text-secondary)]">{label}</span>
    </div>
  );
}

interface WeeklyStatsProps {
  stats: WeeklyStatsData;
  loading?: boolean;
}

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function WeeklyStats({ stats, loading = false }: WeeklyStatsProps) {
  if (loading) {
    return (
      <div className="flex gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="flex-1 h-[88px] rounded-card" />
        ))}
      </div>
    );
  }

  const marksLabel =
    stats.marks_max > 0
      ? `${stats.marks_scored} of ${stats.marks_max}`
      : `${stats.marks_scored}`;

  return (
    <div className="flex flex-wrap gap-3" role="region" aria-label="Weekly stats">
      <StatCell
        value={String(stats.sessions_this_week)}
        label="Sessions"
      />
      <StatCell
        value={String(stats.questions_attempted)}
        label="Questions"
      />
      <StatCell
        value={marksLabel}
        label="Marks scored"
      />
      <StatCell
        value={formatMinutes(stats.time_in_app_minutes)}
        label="Time in app"
      />
    </div>
  );
}
