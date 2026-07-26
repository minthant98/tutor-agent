"use client";

import { useRouter } from "next/navigation";
import { capture } from "@/lib/analytics";

interface Recommendation {
  topic_id: string;
  sub_skill: string;
  blurb: string;
}

interface RecommendedNextStepProps {
  submissionId: string;
  recommendation: Recommendation;
}

/**
 * RecommendedNextStep — Task 27 Marker→Practice bridge block.
 *
 * Rendered above the actions row when the backend returns a non-null
 * recommended_practice for a graded submission.
 *
 * Design spec (Stride visual brief: 50% Linear / 30% Raycast / 20% Headspace):
 * - Section header: Geist Sans 14 text-secondary
 * - Blurb: Geist Sans 16
 * - Primary CTA "Start Practice": fires PostHog + deep-links to practice drill-in
 */
export function RecommendedNextStep({
  submissionId,
  recommendation,
}: RecommendedNextStepProps) {
  const router = useRouter();
  const { topic_id, sub_skill, blurb } = recommendation;

  function handleStartPractice() {
    capture("marker_recommended_practice_clicked", {
      submission_id: submissionId,
      topic_id,
      sub_skill,
    });
    router.push(
      `/practice/plan?mode=drill_in&topic=${encodeURIComponent(topic_id)}&skill=${encodeURIComponent(sub_skill)}&submission_id=${encodeURIComponent(submissionId)}`
    );
  }

  return (
    <div
      data-testid="recommended-next-step"
      className="rounded-xl border border-border bg-card px-5 py-4 space-y-3"
    >
      {/* Section header */}
      <p className="font-sans text-[14px] text-muted-foreground leading-none">
        Recommended next step
      </p>

      {/* Blurb */}
      <p
        data-testid="recommended-blurb"
        className="font-sans text-[16px] text-foreground leading-snug"
      >
        {blurb}
      </p>

      {/* Primary CTA */}
      <button
        type="button"
        onClick={handleStartPractice}
        className="inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2 font-sans text-[14px] font-medium text-background transition-opacity hover:opacity-80 active:opacity-70"
      >
        Start Practice
      </button>
    </div>
  );
}
