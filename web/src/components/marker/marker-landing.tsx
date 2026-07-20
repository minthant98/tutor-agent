"use client";
import type { MarkerV3LandingData } from "@/lib/types";
import { SuggestedQuestionCard } from "./suggested-question-card";
import { RecentSubmissionsList } from "./recent-submissions-list";

interface MarkerLandingProps {
  data: MarkerV3LandingData;
  onRefresh: () => void;
}

export function MarkerLanding({ data, onRefresh }: MarkerLandingProps) {
  return (
    <div className="space-y-6">
      {/* Alex narration line */}
      <p
        className="border-l-2 border-readiness-2 pl-3 font-sans text-[14px] text-[var(--text-secondary)] leading-relaxed"
        data-testid="alex-narration"
      >
        {data.narration}
      </p>

      {/* Suggested question card */}
      <SuggestedQuestionCard
        question={data.question}
        refreshCountUsed={data.refresh_count_used}
        refreshLimit={data.refresh_limit}
        tier={data.tier}
        onRefresh={onRefresh}
      />

      {/* Recent submissions */}
      <section aria-labelledby="recent-submissions-heading">
        <h2
          id="recent-submissions-heading"
          className="mb-3 text-[13px] font-medium uppercase tracking-wider text-[var(--text-secondary)]"
        >
          Recent submissions
        </h2>
        <RecentSubmissionsList submissions={data.recent_submissions} />
      </section>
    </div>
  );
}
