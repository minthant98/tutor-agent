"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { practiceApi } from "@/lib/api/practice";
import { useFeatureFlag } from "@/lib/feature-flags";
import type { TopicMasteryOut } from "@/lib/types";

interface TopicsListProps {
  strong: TopicMasteryOut[];
  weak: TopicMasteryOut[];
  subject: string;
}

export function TopicsList({ strong, weak, subject }: TopicsListProps) {
  const router = useRouter();
  const practiceEnabled = useFeatureFlag("practice_v2", true);
  const [starting, setStarting] = useState<string | null>(null);

  const startDrill = async (topic: string, mastery_pct: number) => {
    if (starting) return;
    setStarting(topic);
    try {
      posthog.capture("weak_topic_tapped", { topic, mastery_pct });
    } catch {}
    try {
      const s = await practiceApi.startDrillIn(subject, topic);
      router.push(`/session/${s.session_id}`);
    } catch {
      setStarting(null);
    }
  };

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
          ) : practiceEnabled ? (
            weak.map((t) => (
              <li key={t.topic}>
                <button
                  onClick={() => startDrill(t.topic, t.mastery_pct)}
                  disabled={starting === t.topic}
                  className="flex w-full items-center justify-between rounded px-1 py-0.5 text-left hover:bg-gray-50 disabled:opacity-50"
                >
                  <span>⚠ {t.topic_name} · {t.mastery_pct}%</span>
                  <span className="text-[var(--text-secondary)]">
                    {starting === t.topic ? "…" : "→"}
                  </span>
                </button>
              </li>
            ))
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
