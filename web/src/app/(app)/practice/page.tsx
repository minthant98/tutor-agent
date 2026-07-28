"use client";

import { useFeatureFlag } from "@/lib/feature-flags";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { usePracticeNarration } from "@/hooks/use-practice-narration";
import { PracticeLanding } from "@/components/practice/practice-landing";

// ── Skeleton shown while v3 data loads ──────────────────────────────────────

function PracticeSkeleton() {
  return (
    <div className="max-w-[1120px] mx-auto pt-12 px-6 space-y-8 animate-pulse">
      <div className="h-4 w-3/4 rounded bg-[var(--surface-2)]" />
      <div className="h-8 w-1/2 rounded bg-[var(--surface-2)]" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-[280px] rounded-card bg-[var(--surface-2)]" />
        ))}
      </div>
    </div>
  );
}

// ── v3 view — fetches narration + weak topics ────────────────────────────────

function PracticeV3View({ subject }: { subject: string }) {
  const { data, isLoading } = usePracticeNarration(subject);
  if (isLoading || !data) return <PracticeSkeleton />;
  // TODO(task-17): pass real topics from useTopics() hook once available.
  // Using empty array for now — Drill-In Start button stays disabled until wired.
  return <PracticeLanding data={data} topics={[]} />;
}

// ── Legacy v2 placeholder ────────────────────────────────────────────────────

function LegacyPracticePage() {
  return (
    <div className="max-w-[960px] mx-auto pt-12 px-4">
      <p className="text-[var(--text-secondary)]">
        Practice mode is being upgraded. Enable the <code>practice_v3</code> flag to use the new
        landing page.
      </p>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function PracticePage() {
  const v3 = useFeatureFlag("practice_v3", false);
  const { subject } = useCurrentSubject();

  if (v3) return <PracticeV3View subject={subject} />;
  return <LegacyPracticePage />;
}
