"use client";

import Link from "next/link";
import { Check, AlertTriangle, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface HistoryRowItem {
  id: string;
  status: "pending" | "extracting" | "grading" | "graded" | "error";
  marks?: number | null;
  max_marks: number;
  delta?: number | null;
  question_preview: string;
  topic?: string | null;
  created_at: string;
}

function StatusIcon({ status }: { status: HistoryRowItem["status"] }) {
  if (status === "graded") {
    return (
      <Check
        aria-label="Graded"
        size={16}
        className="shrink-0 text-[var(--semantic-success-text)]"
      />
    );
  }
  if (status === "error") {
    return (
      <AlertTriangle
        aria-label="Extraction failed"
        size={16}
        className="shrink-0 text-[var(--semantic-warning-text)]"
      />
    );
  }
  // pending | extracting | grading
  return (
    <Clock
      aria-label="Pending"
      size={16}
      className="shrink-0 text-[var(--text-secondary)]"
    />
  );
}

function DeltaPill({ delta }: { delta: number }) {
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

export function HistoryRow({ item }: { item: HistoryRowItem }) {
  const date = new Date(item.created_at).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const preview =
    item.question_preview.length > 80
      ? item.question_preview.slice(0, 80) + "…"
      : item.question_preview;

  return (
    <Link
      href={`/mark/${item.id}`}
      className="flex h-16 items-center gap-3 rounded-card border border-[var(--border-subtle)] bg-[var(--surface-2)] px-4 hover:bg-[var(--surface-1)] transition-colors duration-fast"
    >
      {/* Status icon */}
      <StatusIcon status={item.status} />

      {/* Date */}
      <span className="w-[90px] shrink-0 font-sans text-[12px] text-[var(--text-secondary)]">
        {date}
      </span>

      {/* Question preview + topic */}
      <span className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
        <span className="truncate font-sans text-[14px] text-[var(--text-primary)]">
          {preview}
        </span>
        {item.topic && (
          <Badge variant="secondary" className="shrink-0 text-[11px]">
            {item.topic.replace(/_/g, " ")}
          </Badge>
        )}
      </span>

      {/* Marks + delta */}
      {item.status === "graded" && item.marks != null && (
        <span className="flex shrink-0 items-center gap-1.5">
          <span className="font-mono text-[14px] font-semibold text-[var(--text-primary)]">
            {item.marks}/{item.max_marks}
          </span>
          {item.delta != null && <DeltaPill delta={item.delta} />}
        </span>
      )}
    </Link>
  );
}
