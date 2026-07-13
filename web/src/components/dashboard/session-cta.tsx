"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

interface ResumeState {
  segment_index: number;
  minutes_remaining: number;
}

interface SessionCtaProps {
  resumeState: ResumeState | null;
  totalSegments: number;
}

export function SessionCta({ resumeState, totalSegments }: SessionCtaProps) {
  const router = useRouter();
  const href = "/sessions/today";
  const go = useCallback(() => router.push(href), [router, href]);

  useKeyboardShortcut("Enter", go, { ignoreInInput: true });
  useKeyboardShortcut(" ", go, { ignoreInInput: true });

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <Button variant="primary" size="lg" onClick={go}>
        {resumeState ? "Resume Today's Session" : "Start Today's Session"}
      </Button>
      {resumeState && (
        <p className="font-sans text-[12px] text-[var(--text-secondary)]">
          Segment {resumeState.segment_index + 1} of {totalSegments} &middot;{" "}
          {resumeState.minutes_remaining} minutes remaining
        </p>
      )}
      <span className="font-mono text-[12px] text-[var(--text-secondary)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)]">
        ↵
      </span>
    </div>
  );
}
