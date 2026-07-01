import type { TopicMasteryOut } from "@/lib/types";

interface TopicsListProps {
  strong: TopicMasteryOut[];
  weak: TopicMasteryOut[];
}

export function TopicsList({ strong, weak }: TopicsListProps) {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Strong</h3>
        <ul className="space-y-1 text-sm">
          {strong.length === 0 ? (
            <li className="text-[var(--text-secondary)]">Nothing yet — keep practising.</li>
          ) : (
            strong.map((t) => (
              <li key={t.topic}>
                ✓ {t.topic_name} · {t.mastery_pct}%
              </li>
            ))
          )}
        </ul>
      </div>
      <div className="rounded-lg border border-[var(--border)] bg-white p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase text-[var(--text-secondary)]">Needs work</h3>
        <ul className="space-y-1 text-sm">
          {weak.length === 0 ? (
            <li className="text-[var(--text-secondary)]">All clear for now.</li>
          ) : (
            weak.map((t) => (
              <li key={t.topic}>
                ⚠ {t.topic_name} · {t.mastery_pct}%
              </li>
            ))
          )}
        </ul>
      </div>
    </section>
  );
}
