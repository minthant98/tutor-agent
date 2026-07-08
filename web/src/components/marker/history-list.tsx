"use client";
import Link from "next/link";
import type { SubmissionOut } from "@/lib/types";

export function HistoryList({ items }: { items: SubmissionOut[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-[var(--text-secondary)]">
        No marked work yet. Head over to Mark my work to try it.
      </p>
    );
  }
  return (
    <ul className="divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] bg-white">
      {items.map((item) => {
        const date = new Date(item.created_at).toLocaleDateString();
        const pct = item.grade_pct !== null ? Math.round(item.grade_pct) : null;
        return (
          <li key={item.id}>
            <Link
              href={`/mark/history/${item.id}`}
              className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
            >
              <span className="text-sm">
                {date} · {item.question_text.slice(0, 60)}
                {item.question_text.length > 60 && "…"}
              </span>
              {pct !== null && (
                <span className="text-sm font-semibold">
                  {item.marks_awarded}/{item.max_marks} ({pct}%)
                </span>
              )}
              {item.status === "error" && (
                <span className="text-sm text-red-600">error</span>
              )}
              {["pending", "extracting", "grading"].includes(item.status) && (
                <span className="text-sm text-[var(--text-secondary)]">grading…</span>
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
