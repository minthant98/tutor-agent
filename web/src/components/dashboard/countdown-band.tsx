import Link from "next/link";
import type { DashboardPayload } from "@/lib/types";

export function CountdownBand({ data }: { data: DashboardPayload }) {
  const days = data.days_until_exam;
  const dateLabel = (() => {
    if (days === null || days === undefined) return "Estimated: ~6 months";
    if (days < 0) return "Exam has passed";
    if (days > 365) return "1 year+ until exam";
    return `Pure Maths exam — ${days} days remaining`;
  })();

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-4">
      <p className="text-sm text-[var(--text-secondary)]">
        {dateLabel}
        {days !== null && days !== undefined && days < 0 && (
          <Link href="/account#academic" className="ml-2 text-[var(--blue)]">
            Set a new date →
          </Link>
        )}
      </p>
      <div className="mt-2 flex items-center gap-6">
        <div>
          <dt className="text-xs text-[var(--text-secondary)]">Target</dt>
          <dd className="text-lg font-semibold">{data.target_grade}</dd>
        </div>
        {data.predicted_grade && (
          <div>
            <dt className="text-xs text-[var(--text-secondary)]">Current prediction</dt>
            <dd className="text-lg font-semibold">
              {data.predicted_grade}
              <span className="ml-1 text-xs font-normal text-[var(--text-secondary)]">est.</span>
            </dd>
          </div>
        )}
      </div>
    </section>
  );
}
