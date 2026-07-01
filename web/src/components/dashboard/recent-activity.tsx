import type { RecentActivityOut } from "@/lib/types";

export function RecentActivity({ data }: { data: RecentActivityOut }) {
  if (data.cold) {
    return (
      <p className="text-sm text-[var(--text-secondary)]">
        You haven&apos;t studied in a few days. Let&apos;s get back on track.
      </p>
    );
  }
  if (!data.last_studied) return null;
  return (
    <p className="text-sm text-[var(--text-secondary)]">
      Last studied: {data.last_studied} · {data.summary}
    </p>
  );
}
