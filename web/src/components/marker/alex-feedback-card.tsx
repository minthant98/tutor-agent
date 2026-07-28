"use client";
import type { MemoryRef } from "@/lib/types";

interface AlexFeedbackCardProps {
  improvement: string;
  memoryRef?: MemoryRef | null;
}

/**
 * AlexFeedbackCard — Alex's improvement paragraph + optional memory reference.
 *
 * Surface 1 with left border using the educational alex-feedback token.
 * Memory reference line only renders when memoryRef is non-null.
 */
export function AlexFeedbackCard({ improvement, memoryRef }: AlexFeedbackCardProps) {
  return (
    <div
      className="bg-[var(--surface-1)] border-l-[3px] border-[var(--color-alex-feedback)] rounded-r-card p-5"
      data-testid="alex-feedback-card"
    >
      {/* Improvement paragraph — Geist Sans 16 */}
      <p className="font-sans text-[16px] text-[var(--text-primary)] leading-relaxed">
        {improvement}
      </p>

      {/* Memory reference — only when evidence exists */}
      {memoryRef && (
        <p
          className="font-sans text-[14px] text-[var(--text-secondary)] mt-2"
          data-testid="alex-memory-ref"
        >
          {memoryRef.text}
        </p>
      )}
    </div>
  );
}
