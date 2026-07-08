"use client";
import type { SubmissionOut } from "@/lib/types";

const GRADE_TIER = (pct: number) => {
  if (pct >= 70) return { color: "text-emerald-700", bg: "bg-emerald-50" };
  if (pct >= 40) return { color: "text-amber-700", bg: "bg-amber-50" };
  return { color: "text-red-700", bg: "bg-red-50" };
};

export function ResultsView({
  submission,
  examDate,
  predictedGrade,
  daysUntilExam,
  onMarkAnother,
  onDashboard,
  readonly = false,
}: {
  submission: SubmissionOut;
  examDate?: string | null;
  predictedGrade?: string | null;
  daysUntilExam?: number | null;
  onMarkAnother?: () => void;
  onDashboard?: () => void;
  readonly?: boolean;
}) {
  const fb = submission.feedback_json;
  const pct = submission.grade_pct ?? 0;
  const tier = GRADE_TIER(pct);
  const delta = fb?.readiness_delta ?? 0;

  return (
    <div className="space-y-4">
      <section className={`rounded-lg p-5 ${tier.bg}`}>
        <div className={`text-3xl font-semibold ${tier.color}`}>
          {submission.marks_awarded} / {submission.max_marks} marks · {Math.round(pct)}%
        </div>
        {fb && delta !== 0 && (
          <p className="mt-2 text-sm text-emerald-700">
            {fb.readiness_before}% → {fb.readiness_after}%
            {" "}({delta > 0 ? "+" : ""}{delta.toFixed(1)}%)
          </p>
        )}
        {daysUntilExam !== undefined && daysUntilExam !== null && (
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {daysUntilExam} days until exam
            {predictedGrade && ` · You're on track for a ${predictedGrade}`}
          </p>
        )}
      </section>

      {fb && (
        <>
          <details className="rounded-lg border border-[var(--border)] bg-white p-4">
            <summary className="cursor-pointer text-sm font-semibold">
              Question
            </summary>
            <p className="mt-2 whitespace-pre-wrap text-sm">
              {submission.question_text}
            </p>
          </details>

          <section className="rounded-lg border border-[var(--border)] bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">
              Criteria
            </h3>
            <ul className="space-y-2">
              {fb.criteria.map((c, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className={c.awarded ? "text-emerald-600" : "text-slate-400"}>
                    {c.awarded ? "✓" : "✗"}
                  </span>
                  <div>
                    <div className="font-medium">
                      [{c.code}] {c.description}
                    </div>
                    {c.comment && (
                      <div className="text-[var(--text-secondary)]">
                        {c.comment}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-lg bg-blue-50 p-4 text-sm">
            <p className="font-semibold text-[var(--blue)]">Summary</p>
            <p className="mt-1">{fb.summary}</p>
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-white p-4 text-sm">
            <p className="font-semibold">To improve</p>
            <p className="mt-1">{fb.improvement}</p>
          </section>
        </>
      )}

      {submission.answer_text && (
        <details className="rounded-lg border border-[var(--border)] bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold">
            View your answer
          </summary>
          <p className="mt-2 whitespace-pre-wrap text-sm">
            {submission.answer_text}
          </p>
          {submission.photo_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={submission.photo_url}
              alt="your answer"
              className="mt-2 max-h-96 rounded-md border border-[var(--border)]"
            />
          )}
        </details>
      )}

      {!readonly && (
        <div className="flex gap-3">
          <button
            onClick={onMarkAnother}
            className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
          >
            Mark another question
          </button>
          <button
            onClick={onDashboard}
            className="rounded-lg border border-[var(--border)] px-4 py-2"
          >
            Return to dashboard
          </button>
        </div>
      )}
    </div>
  );
}
