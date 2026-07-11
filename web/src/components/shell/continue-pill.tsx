"use client";
import Link from "next/link";
import { PlayCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useActiveSession } from "@/hooks/use-active-session";

/** Convert a snake_case topic id into a human-readable label. */
function formatTopicLabel(topic: string | null): string {
  if (!topic) return "Session";
  return topic
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Build copy per spec:
 * - quick_practice / weak_areas / drill_in / marker → "<Topic> · Question N / total"
 * - teach / reinforce / other → "<Topic> · N min remaining"
 */
function buildCopy(
  topic: string | null,
  sessionType: string,
  progress: { current_question?: number; total_questions?: number; minutes_remaining?: number }
): string {
  const topicLabel = formatTopicLabel(topic);

  if (["quick_practice", "weak_areas", "drill_in", "marker"].includes(sessionType)) {
    const q = progress.current_question ?? 1;
    const total = progress.total_questions ?? 0;
    return `${topicLabel} · Question ${q} / ${total}`;
  }

  // teach / reinforce / practice / diagnostic
  const mins = progress.minutes_remaining ?? 0;
  return `${topicLabel} · ${mins} min remaining`;
}

interface ContinuePillProps {
  collapsed?: boolean;
}

export function ContinuePill({ collapsed }: ContinuePillProps) {
  const session = useActiveSession();

  if (!session) return null;

  const copy = buildCopy(session.topic, session.session_type, session.progress);

  return (
    <div className="px-2 pb-2">
      <Link
        href={`/session/${session.session_id}`}
        className={cn(
          "group flex items-center gap-2 rounded-input border border-[var(--border-subtle)]",
          "bg-[var(--surface-1)] px-3 py-2 transition-colors duration-fast",
          "hover:bg-[var(--surface-2)] hover:border-[var(--primary)]",
          collapsed && "justify-center px-2"
        )}
        title={collapsed ? copy : undefined}
      >
        <PlayCircle
          className="h-4 w-4 shrink-0 text-[var(--primary)]"
          aria-hidden
        />
        {!collapsed && (
          <div className="min-w-0 flex-1 overflow-hidden">
            <p className="text-11 font-sans font-medium text-[var(--text-muted)] uppercase tracking-wide leading-none mb-0.5">
              Continue
            </p>
            <p className="text-12 font-sans text-[var(--text-primary)] truncate leading-none">
              {copy}
            </p>
          </div>
        )}
      </Link>
    </div>
  );
}
