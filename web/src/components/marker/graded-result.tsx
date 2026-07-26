"use client";
import type { SubmissionOut } from "@/lib/types";
import { capture } from "@/lib/analytics";
import { ResultHero } from "./result-hero";
import { AlexFeedbackCard } from "./alex-feedback-card";
import { CriteriaBreakdown } from "./criteria-breakdown";
import { MarkSchemeAccordion } from "./mark-scheme-accordion";
import { RecommendedNextStep } from "./recommended-next-step";

interface GradedResultProps {
  submission: SubmissionOut;
  targetGrade?: string;
  /** Raw mark scheme text for the accordion (Task 26). Passed by the host page when available. */
  markScheme?: string;
}

/**
 * GradedResult — flagship post-submission result screen (Task 25).
 *
 * Composition:
 *   ResultHero — marks hero + readiness delta
 *   AlexFeedbackCard — improvement paragraph + optional memory reference
 *   CriteriaBreakdown — per-criterion awarded/not-awarded table (Task 26)
 *   MarkSchemeAccordion — collapsible mark scheme, auto-scrolls to first gap (Task 26)
 *   [placeholder] Task 27: recommended next step
 */
export function GradedResult({ submission, targetGrade = "A", markScheme }: GradedResultProps) {
  const fb = submission.feedback_json;
  const marks = submission.marks_awarded ?? 0;
  const maxMarks = submission.max_marks;
  const gradePct = submission.grade_pct ?? 0;

  // Readiness: prefer top-level fields (Task 25 backend), fall back to feedback_json
  const readinessBefore =
    submission.readiness_before ??
    (fb?.readiness_before ?? 0);
  const readinessAfter =
    submission.readiness_after ??
    (fb?.readiness_after ?? 0);

  return (
    <div className="mx-auto max-w-[880px] pt-12 px-6 space-y-6">
      {/* Hero: marks + readiness delta */}
      <ResultHero
        marks={marks}
        maxMarks={maxMarks}
        gradePct={gradePct}
        readinessBefore={readinessBefore}
        readinessAfter={readinessAfter}
        targetGrade={targetGrade}
      />

      {/* Alex feedback: improvement + memory reference */}
      {fb && (
        <AlexFeedbackCard
          improvement={fb.improvement}
          memoryRef={submission.memory_ref}
        />
      )}

      {/* Criteria breakdown (Task 26) */}
      {fb?.criteria && fb.criteria.length > 0 && (
        <CriteriaBreakdown criteria={fb.criteria} />
      )}

      {/* Mark scheme accordion (Task 26) */}
      {fb && markScheme && (
        <MarkSchemeAccordion
          scheme={markScheme}
          firstNotAwardedRef={
            // First criterion not awarded, if any — drives auto-scroll on open
            fb.criteria?.find((c) => !c.awarded)?.code ?? null
          }
        />
      )}

      {/* Task 27: Recommended next step — mounted above the actions row when present */}
      {submission.recommended_practice && (
        <RecommendedNextStep
          submissionId={submission.id}
          recommendation={submission.recommended_practice}
        />
      )}

      {/* Actions row */}
      <div className="flex gap-3 pt-2">
        {submission.recommended_practice ? (
          /* When a recommendation exists: only ghost "Try a similar question" */
          <button
            type="button"
            onClick={() => capture("marker_try_similar_clicked", { submission_id: submission.id })}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-transparent px-4 py-2 font-sans text-[14px] font-medium text-foreground transition-opacity hover:opacity-70"
          >
            Try a similar question
          </button>
        ) : (
          /* No recommendation: "Try a similar question" is the primary CTA */
          <button
            type="button"
            onClick={() => capture("marker_try_similar_clicked", { submission_id: submission.id })}
            className="inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2 font-sans text-[14px] font-medium text-background transition-opacity hover:opacity-80 active:opacity-70"
          >
            Try a similar question
          </button>
        )}
      </div>
    </div>
  );
}
