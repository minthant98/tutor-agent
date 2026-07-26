"use client";

import Link from "next/link";
import type { SubmissionOut } from "@/lib/types";
import { HistoryRow } from "@/components/marker/history-row";

interface HistoryListProps {
  items: SubmissionOut[];
  hasMore?: boolean;
  onShowMore?: () => void;
  loadingMore?: boolean;
}

export function HistoryList({
  items,
  hasMore = false,
  onShowMore,
  loadingMore = false,
}: HistoryListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-12 text-center">
        <p className="text-[14px] text-[var(--text-secondary)]">
          No graded submissions yet. Submit your first answer to see it here.
        </p>
        <Link
          href="/mark/new"
          className="inline-flex items-center rounded-full bg-[var(--primary)] px-4 py-2 text-[14px] font-medium text-white transition-opacity hover:opacity-90"
        >
          Submit your first answer
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item) => {
        // Build delta from readiness fields if available
        const delta =
          item.readiness_before != null && item.readiness_after != null
            ? Math.round(item.readiness_after - item.readiness_before)
            : null;

        return (
          <HistoryRow
            key={item.id}
            item={{
              id: item.id,
              status: item.status,
              marks: item.marks_awarded,
              max_marks: item.max_marks,
              delta,
              question_preview: item.question_text,
              topic: null, // TODO: expose topic from GradedUpload once column exists
              created_at: item.created_at,
            }}
          />
        );
      })}

      {hasMore && (
        <button
          onClick={onShowMore}
          disabled={loadingMore}
          className="mt-2 w-full rounded-card border border-[var(--border-subtle)] bg-transparent px-4 py-2.5 text-[14px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] disabled:opacity-50"
        >
          {loadingMore ? "Loading…" : "Show more"}
        </button>
      )}
    </div>
  );
}
