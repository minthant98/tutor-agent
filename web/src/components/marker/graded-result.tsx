"use client";
import type { SubmissionOut } from "@/lib/types";
import { ResultHero } from "./result-hero";
import { AlexFeedbackCard } from "./alex-feedback-card";
import { CriteriaBreakdown } from "./criteria-breakdown";
import { MarkSchemeAccordion } from "./mark-scheme-accordion";

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

      {/* TODO(Task 27): recommended next step goes here */}
      {/* <div data-slot="recommended-next-step" /> */}
    </div>
  );
}
