import type { DashboardPayload } from "@/lib/types";

export function ReadinessCard({ data }: { data: DashboardPayload }) {
  const pct = Math.round(data.readiness_pct);

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <h2 className="mb-2 text-xs uppercase tracking-wide text-[var(--text-secondary)]">
        Exam Readiness
      </h2>
      <div className="text-4xl font-semibold">{pct}%</div>
      <div className="mt-3 h-2 overflow-hidden rounded bg-gray-100">
        <div className="h-full bg-[var(--blue)]" style={{ width: `${pct}%` }} />
      </div>
      {data.readiness_trend ? (
        <p className="mt-3 text-sm text-[var(--blue)]">
          {data.readiness_trend.delta >= 0 ? "+" : ""}
          {data.readiness_trend.delta}% this month
        </p>
      ) : (
        <p className="mt-3 text-sm text-[var(--text-secondary)]">
          You&apos;re just getting started — complete a few study sessions and we&apos;ll begin
          tracking your improvement over time.
        </p>
      )}
    </section>
  );
}
