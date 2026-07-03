"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeTopic } from "@/lib/types";

interface Props {
  subject: string;
  onClose: () => void;
}

export function QuickPracticeModal({ subject, onClose }: Props) {
  const router = useRouter();
  const [topics, setTopics] = useState<PracticeTopic[] | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [errored, setErrored] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    practiceApi
      .getTopics(subject)
      .then((rows) => {
        setTopics(rows);
        if (rows.length > 0) setSelected(rows[0].topic_id);
      })
      .catch(() => setErrored(true));
  }, [subject]);

  const start = async () => {
    if (!selected) return;
    setStarting(true);
    try {
      const s = await practiceApi.startQuick(subject, selected);
      router.push(`/session/${s.session_id}`);
    } catch {
      setStarting(false);
      setErrored(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Quick Practice</h3>

        {errored && (
          <p className="mb-3 text-sm text-red-600">
            Couldn&apos;t load topics — try again.
          </p>
        )}

        {topics === null && !errored && (
          <p className="text-sm text-[var(--text-secondary)]">Loading topics…</p>
        )}

        {topics !== null && topics.length > 0 && (
          <label className="block text-sm">
            Pick a topic
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--border)] px-3 py-2"
            >
              {topics.map((t) => (
                <option key={t.topic_id} value={t.topic_id}>
                  {t.topic_name} — {t.has_attempts ? `${t.mastery_pct}%` : "New"}
                </option>
              ))}
            </select>
          </label>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-[var(--border)] px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={start}
            disabled={!selected || starting || topics === null}
            className="rounded-md bg-[var(--blue)] px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {starting ? "Starting…" : "Start"}
          </button>
        </div>
      </div>
    </div>
  );
}
