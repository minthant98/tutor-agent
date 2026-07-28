import Link from "next/link";
import { TopicCard } from "./topic-card";
import type { TopicV3 } from "./types";

interface TopicsGridProps {
  topics: TopicV3[];
  /** Filtered list to display (after client-side filter application). */
  filtered: TopicV3[];
}

export function TopicsGrid({ topics, filtered }: TopicsGridProps) {
  if (topics.length === 0) {
    return (
      <div className="py-16 text-center text-[var(--text-secondary)]">
        <p>No topics for this subject yet.</p>
        <Link
          href="/practice"
          className="mt-2 inline-block text-[14px] underline text-[var(--text-primary)]"
        >
          Back to Practice
        </Link>
      </div>
    );
  }

  const mastered = topics.filter((t) => t.status === "Mastered").length;
  const needsRevision = topics.filter(
    (t) => t.status === "Needs review" || t.status === "Practising"
  ).length;
  const notCovered = topics.filter((t) => t.status === "Not started").length;

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <p className="text-[13px] text-[var(--text-secondary)]">
        <span className="font-mono">{topics.length}</span> topics ·{" "}
        <span className="font-mono">{mastered}</span> mastered ·{" "}
        <span className="font-mono">{needsRevision}</span> needing revision ·{" "}
        <span className="font-mono">{notCovered}</span> not yet covered
      </p>

      {/* Grid */}
      {filtered.length === 0 ? (
        <p className="text-[var(--text-secondary)] text-[14px]">
          No topics match the current filters.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {filtered.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      )}
    </div>
  );
}
