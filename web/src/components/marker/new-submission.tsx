"use client";

import { capture } from "@/lib/analytics";
import { MarkSchemePeek } from "./mark-scheme-peek";
import type { MarkerV3Question } from "@/lib/types";

export interface NewSubmissionProps {
  question: MarkerV3Question & { mark_scheme: string };
  onSubmit?: (answerText: string) => void;
}

export function NewSubmission({ question, onSubmit: _onSubmit }: NewSubmissionProps) {
  return (
    <div className="mx-auto max-w-[880px] pt-12 px-6 space-y-6">
      {/* 1. Question */}
      <section
        className="border-l-[3px] border-[var(--color-question)] pl-4 space-y-2"
        aria-label="Question"
      >
        <div className="flex items-start justify-between gap-3">
          <p className="text-16 leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap flex-1">
            {question.text}
          </p>
          <span className="shrink-0 rounded-full bg-[var(--color-question)]/10 px-2.5 py-0.5 text-12 font-mono font-semibold text-[var(--color-question)] mt-0.5">
            {question.max_marks} marks
          </span>
        </div>
        <p className="text-12 text-[var(--text-secondary)]">{question.paper_ref}</p>
      </section>

      {/* 2. Mark scheme peek */}
      <MarkSchemePeek
        scheme={question.mark_scheme}
        onEventPreReveal={() => capture("marker_mark_scheme_pre_reveal", { question_id: question.id })}
      />

      {/* 3. Answer area — placeholder (Task 28 wires input mode toggle + Textarea) */}
      <section aria-label="Your answer">
        <div className="rounded-card border border-border-subtle bg-surface-1 p-4 min-h-[140px] flex items-center justify-center">
          <p className="text-12 text-[var(--text-secondary)]">Answer input coming soon (Task 28)</p>
        </div>
      </section>
    </div>
  );
}
