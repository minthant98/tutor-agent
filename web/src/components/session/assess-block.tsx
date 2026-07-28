"use client";

export type AssessQuestion = {
  text: string;
  max_marks: number;
};

interface AssessBlockProps {
  question: AssessQuestion;
}

/**
 * AssessBlock — renders an assessment question card.
 *
 * Layout: 880px max-width centered. Left accent border in `question` color.
 * Marks chip top-right in Geist Mono 12. Question text below in 16px body.
 *
 * NOTE: No answer input — that is Task 11 (AnswerInput).
 */
export function AssessBlock({ question }: AssessBlockProps) {
  return (
    <section
      aria-label="Question"
      className="max-w-[880px] mx-auto"
    >
      <div className="relative border-l-[3px] border-[var(--color-question)] bg-[var(--surface-1)] rounded-r-lg p-6">
        {/* Marks chip — top right */}
        <span className="absolute top-4 right-4 font-mono text-[12px] text-[var(--text-secondary)] tracking-tight">
          [{question.max_marks} marks]
        </span>

        {/* Question text */}
        <p className="text-[16px] font-sans leading-[1.6] text-[var(--text-primary)] pr-20">
          {question.text}
        </p>
      </div>
    </section>
  );
}
