"use client";

import { AlexNarration } from "./alex-narration";
import { ReadinessSnapshot } from "./readiness-snapshot";
import { SegmentCards } from "./segment-cards";
import { SessionCta } from "./session-cta";

export interface DashboardV3Segment {
  intent: string;
  topic: string;
  why: string;
  minutes: number;
  questions: number;
  sub_skills?: string[];
  learning_objective?: string;
}

export interface DashboardV3ResumeState {
  segment_index: number;
  minutes_remaining: number;
}

export interface DashboardV3Payload {
  narration: string;
  readiness_snapshot: {
    percent: number;
    band: "A*" | "A" | "B" | "C";
    target_grade: string;
    days_to_exam: number | null;
  };
  session_plan: DashboardV3Segment[];
  total_minutes: number;
  resume_state: DashboardV3ResumeState | null;
}

interface DashboardHeroProps {
  data: DashboardV3Payload;
}

export function DashboardHero({ data }: DashboardHeroProps) {
  return (
    <div className="max-w-[960px] mx-auto pt-12 px-4 space-y-12">
      {/* Alex narration — left border colored by readiness band */}
      <AlexNarration text={data.narration} band={data.readiness_snapshot.band} />

      {/* Readiness snapshot */}
      <ReadinessSnapshot snapshot={data.readiness_snapshot} />

      {/* Session commitment block */}
      <div className="space-y-6">
        <div className="text-center">
          <div className="font-sans text-[14px] text-[var(--text-secondary)]">
            Today&apos;s Session
          </div>
          <div className="font-mono text-[16px] text-[var(--text-primary)] mt-1">
            {data.total_minutes} minutes &middot; {data.session_plan.length} segments
          </div>
        </div>

        {/* Segment cards */}
        <SegmentCards segments={data.session_plan} />
      </div>

      {/* Session CTA */}
      <div className="text-center">
        <SessionCta
          resumeState={data.resume_state}
          totalSegments={data.session_plan.length}
        />
      </div>
    </div>
  );
}
