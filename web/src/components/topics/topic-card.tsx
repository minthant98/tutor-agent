"use client";

import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { PrerequisiteLink } from "./prerequisite-link";
import type { TopicV3 } from "./types";

/** Map mastery % to a readiness-N color index (0=Mastered → 4=Not started). */
function bandIndex(mastery: number): number {
  if (mastery >= 70) return 0;   // Mastered — strong blue
  if (mastery >= 40) return 1;   // Practising — mid blue
  if (mastery > 0)   return 3;   // Needs review — amber
  return 4;                       // Not started — orange
}

/** Map status to Badge variant for semantic coloring. */
function statusVariant(status: TopicV3["status"]): "success" | "default" | "warning" | "secondary" {
  switch (status) {
    case "Mastered":      return "success";
    case "Practising":    return "default";
    case "Needs review":  return "warning";
    case "Not started":   return "secondary";
  }
}

interface TopicCardProps {
  topic: TopicV3;
}

export function TopicCard({ topic }: TopicCardProps) {
  const router = useRouter();
  const idx = bandIndex(topic.mastery);

  return (
    // Use a div + data-href to avoid nested <a> hydration errors
    // (PrerequisiteLink renders its own <a>).
    <div
      role="link"
      tabIndex={0}
      data-href={`/topics/${topic.id}`}
      onClick={() => router.push(`/topics/${topic.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          router.push(`/topics/${topic.id}`);
        }
      }}
      className="rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 space-y-3 hover:border-[var(--border-default)] transition-colors duration-fast cursor-pointer"
    >
      {/* Topic label */}
      <div className="text-[20px] font-sans text-[var(--text-primary)]">
        {topic.label}
      </div>

      {/* Readiness row + underline + last practised */}
      <div className="grid grid-cols-2 gap-y-1">
        <div className="text-[12px] text-[var(--text-secondary)]">Readiness</div>
        <div className="text-[20px] font-mono text-right text-[var(--text-primary)]">
          {topic.mastery}%
        </div>
        {/* 2px underline in the readiness gradient color at band */}
        <div
          className="w-full h-[2px] col-span-2"
          style={{ background: `var(--readiness-${idx})` }}
        />
        <div className="text-[12px] text-[var(--text-secondary)]">Last practised</div>
        <div className="text-[12px] text-right text-[var(--text-secondary)]">
          {topic.last_practised}
        </div>
      </div>

      {/* Status badge */}
      <Badge variant={statusVariant(topic.status)}>
        {topic.status}
      </Badge>

      {/* Prerequisite link — only when present */}
      {topic.prerequisite && (
        <div>
          <PrerequisiteLink prerequisite={topic.prerequisite} />
        </div>
      )}
    </div>
  );
}
