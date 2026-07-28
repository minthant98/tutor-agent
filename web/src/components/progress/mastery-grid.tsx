"use client";

import { tokens } from "@/lib/design-tokens";
import { Skeleton } from "@/components/ui/skeleton";

export interface MasteryTopicItem {
  id: string;
  label: string;
  mastery: number;  // 0..100
}

interface MasteryGridProps {
  topics: MasteryTopicItem[];
  loading?: boolean;
}

/** Map mastery % to a 0–4 readiness color index (mirrors TopicCard). */
function bandIndex(mastery: number): number {
  if (mastery >= 70) return 0;   // Strong blue — Mastered
  if (mastery >= 40) return 1;   // Mid blue — Practising
  if (mastery > 0) return 3;     // Amber — Needs review
  return 4;                      // Orange — Not started
}

function MasteryMiniCard({ topic }: { topic: MasteryTopicItem }) {
  const idx = bandIndex(topic.mastery);
  const color = tokens.color.readiness[idx];

  return (
    <div
      className="flex h-20 w-full flex-col justify-between rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] px-3 py-2"
      aria-label={`${topic.label}: ${topic.mastery}% mastery`}
    >
      {/* Topic label */}
      <p
        className="line-clamp-2 font-sans text-[14px] leading-tight text-[var(--text-primary)]"
        title={topic.label}
      >
        {topic.label}
      </p>

      {/* Mastery + confidence underline */}
      <div className="space-y-1">
        <p className="font-mono text-[20px] font-semibold leading-none text-[var(--text-primary)]">
          {topic.mastery}%
        </p>
        {/* 2px confidence-scale underline in readiness gradient color */}
        <div
          className="h-[2px] w-full rounded-full"
          style={{ background: color }}
        />
      </div>
    </div>
  );
}

export function MasteryGrid({ topics, loading = false }: MasteryGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-card" />
        ))}
      </div>
    );
  }

  if (topics.length === 0) {
    return (
      <p className="font-sans text-[14px] text-[var(--text-secondary)]">
        Topics will appear here once you start practising.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {topics.map((t) => (
        <MasteryMiniCard key={t.id} topic={t} />
      ))}
    </div>
  );
}
