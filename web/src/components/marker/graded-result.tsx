"use client";
import type { SubmissionOut } from "@/lib/types";
import { ResultHero } from "./result-hero";
import { AlexFeedbackCard } from "./alex-feedback-card";

interface GradedResultProps {
  submission: SubmissionOut;
  targetGrade?: string;
}

/**
 * GradedResult — flagship post-submission result screen (Task 25).
 *
 * Composition:
 *   ResultHero — marks hero + readiness delta
 *   AlexFeedbackCard — improvement paragraph + optional memory reference
 *   [placeholder] Task 26: criteria breakdown
 *   [placeholder] Task 27: recommended next step
 */
export function GradedResult({ submission, targetGrade = "A" }: GradedResultProps) {
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

      {/* TODO(Task 26): criteria breakdown goes here */}
      {/* <div data-slot="criteria-breakdown" /> */}

      {/* TODO(Task 27): recommended next step goes here */}
      {/* <div data-slot="recommended-next-step" /> */}
    </div>
  );
}
