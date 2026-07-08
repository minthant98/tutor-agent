"use client";
import { useEffect, useState } from "react";
import { practiceApi } from "@/lib/api/practice";
import type { PracticeTopic } from "@/lib/types";

export function TopicPickerModal({
  subject,
  onPick,
  onClose,
}: {
  subject: string;
  onPick: (topic: string) => void;
  onClose: () => void;
}) {
  const [topics, setTopics] = useState<PracticeTopic[] | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [error, setError] = useState(false);

  useEffect(() => {
    practiceApi.getTopics(subject)
      .then((rows) => {
        setTopics(rows);
        if (rows.length > 0) setSelected(rows[0].topic_id);
      })
      .catch(() => setError(true));
  }, [subject]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Pick a topic</h3>
        {error && <p className="text-sm text-red-600">Couldn&apos;t load topics.</p>}
        {topics === null && !error && <p>Loading…</p>}
        {topics && (
          <label className="block text-sm">
            Topic
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
          <button onClick={onClose} className="border border-[var(--border)] rounded-md px-3 py-2 text-sm">
            Cancel
          </button>
          <button
            onClick={() => selected && onPick(selected)}
            disabled={!selected}
            className="rounded-md bg-[var(--blue)] px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Pick
          </button>
        </div>
      </div>
    </div>
  );
}
