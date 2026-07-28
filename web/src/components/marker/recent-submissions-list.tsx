"use client";
import { useRouter } from "next/navigation";
import type { MarkerV3RecentSubmission } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RecentSubmissionsListProps {
  submissions: MarkerV3RecentSubmission[];
}

function DeltaPill({ delta }: { delta: number | null }) {
  if (delta === null) return null;
  const positive = delta >= 0;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium",
        positive
          ? "bg-[var(--semantic-success-bg)] text-[var(--semantic-success-text)]"
          : "bg-[var(--semantic-danger-bg)] text-[var(--semantic-danger-text)]"
      )}
    >
      {positive ? "+" : ""}
      {delta}
    </span>
  );
}

export function RecentSubmissionsList({ submissions }: RecentSubmissionsListProps) {
  const router = useRouter();

  if (submissions.length === 0) {
    return (
      <p className="text-[13px] text-[var(--text-secondary)]">
        No submissions yet. Submit an answer above to see your history here.
      </p>
    );
  }

  return (
    <ul className="space-y-1" role="list" aria-label="Recent submissions">
      {submissions.slice(0, 5).map((sub) => {
        const dateStr = new Date(sub.created_at).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
        });
        return (
          <li
            key={sub.id}
            role="listitem"
            className="flex items-center gap-3 cursor-pointer rounded-card px-3 py-2 hover:bg-[var(--surface-1)] transition-colors duration-fast ease-standard"
            onClick={() => router.push(`/mark/${sub.id}`)}
          >
            {/* Date */}
            <span className="w-16 shrink-0 text-[12px] text-[var(--text-secondary)]">
              {dateStr}
            </span>

            {/* Question preview */}
            <span className="flex-1 truncate text-[13px] text-[var(--text-primary)]">
              {sub.question_preview}
            </span>

            {/* Marks — Geist Mono */}
            <span className="font-mono text-[13px] shrink-0 text-[var(--text-primary)]">
              {sub.marks !== null ? sub.marks : "—"}/{sub.max_marks}
            </span>

            {/* Delta pill */}
            <DeltaPill delta={sub.delta_readiness} />
          </li>
        );
      })}
    </ul>
  );
}
