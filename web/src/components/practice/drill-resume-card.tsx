"use client";

import { Button } from "@/components/ui/button";
import type { DrillResumeData } from "@/lib/api/practice";

export interface DrillResumeCardProps {
  data: DrillResumeData;
  onResume: (sessionId: string) => void;
  onStartOver: () => void;
}

export function DrillResumeCard({ data, onResume, onStartOver }: DrillResumeCardProps) {
  const { session_id, topic_label, progress } = data;

  return (
    <div
      className="border border-[var(--border-subtle)] rounded-[var(--radius-card)] px-5 py-4 space-y-3"
      data-testid="drill-resume-card"
    >
      <div className="space-y-1">
        <p className="text-[12px] font-mono uppercase tracking-wide text-white/60">
          Resume Drill
        </p>
        <p className="text-[16px] font-sans">{topic_label}</p>
        <p className="text-[13px] text-white/60">
          {progress.current}/{progress.total} completed
        </p>
      </div>

      <div className="flex gap-3">
        <Button variant="primary" size="sm" onClick={() => onResume(session_id)}>
          Resume
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onStartOver()}>
          Start over
        </Button>
      </div>
    </div>
  );
}
