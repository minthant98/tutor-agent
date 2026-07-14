"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { practiceApi } from "@/lib/api/practice";
import { useCurrentSubject } from "@/hooks/use-current-subject";
import { PlannerTransparency } from "@/components/practice/planner-transparency";
import type { PlanSegment } from "@/lib/api/practice";

// ── Skeleton ─────────────────────────────────────────────────────────────────

function PlanSkeleton() {
  return (
    <div className="max-w-[640px] mx-auto pt-24 px-6 space-y-8 animate-pulse">
      <div className="h-4 w-3/4 rounded bg-[var(--surface-2)] border-l-2 border-[var(--readiness-2)]" />
      <div className="h-8 w-1/2 rounded bg-[var(--surface-2)]" />
      <div className="border border-[var(--border-subtle)] rounded-[var(--radius-card)] divide-y divide-[var(--border-subtle)]">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex justify-between px-4 py-3">
            <div className="h-4 w-20 rounded bg-[var(--surface-2)]" />
            <div className="h-4 w-32 rounded bg-[var(--surface-2)]" />
          </div>
        ))}
      </div>
      <div className="h-3 w-40 rounded bg-[var(--surface-2)]" />
      <div className="flex gap-3">
        <div className="h-10 w-24 rounded bg-[var(--surface-2)]" />
        <div className="h-10 w-32 rounded bg-[var(--surface-2)]" />
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function PracticePlanPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { subject } = useCurrentSubject();

  const mode = searchParams.get("mode") ?? "weak_areas";
  const topic = searchParams.get("topic");
  const skill = searchParams.get("skill");

  const [narration, setNarration] = useState<string>("");
  const [segments, setSegments] = useState<PlanSegment[]>([]);
  const [minutes, setMinutes] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    practiceApi
      .getPlan(mode, topic, skill)
      .then((data) => {
        setNarration(data.narration);
        setSegments(data.segments);
        setMinutes(data.minutes);
      })
      .catch(() => {
        setError("Failed to load your plan. Please try again.");
      })
      .finally(() => setLoading(false));
  }, [mode, topic, skill]);

  const handleStart = useCallback(async () => {
    try {
      const res = await practiceApi.startSession(subject, mode, topic, skill);
      router.push(`/session/${res.session_id}`);
    } catch {
      // Surface the error inline rather than crashing
      setError("Could not start session. Please try again.");
    }
  }, [router, subject, mode, topic, skill]);

  const handleChangeMode = useCallback(() => {
    router.push("/practice");
  }, [router]);

  if (loading) return <PlanSkeleton />;

  if (error) {
    return (
      <div className="max-w-[640px] mx-auto pt-24 px-6">
        <p className="text-[var(--semantic-danger-text)]">{error}</p>
        <button
          className="mt-4 text-sm text-white/60 underline"
          onClick={() => router.push("/practice")}
        >
          Back to Practice
        </button>
      </div>
    );
  }

  return (
    <PlannerTransparency
      narration={narration}
      segments={segments}
      minutes={minutes}
      onStart={handleStart}
      onChangeMode={handleChangeMode}
    />
  );
}
