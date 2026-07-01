"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { TodayFocusOut, SegmentOut } from "@/lib/types";

function titleFor(s: SegmentOut): string {
  const intent = s.intent[0].toUpperCase() + s.intent.slice(1);
  if (s.topic) return `${intent} ${s.topic.replace(/_/g, " ")}`;
  return intent;
}

export function TodayFocusCard({ data }: { data: TodayFocusOut | null }) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);

  if (!data) return null;

  const start = async () => {
    setStarting(true);
    try {
      const s = await apiFetch<{ id: string }>("/sessions/start", {
        method: "POST",
        body: JSON.stringify({
          subject: "pure_mathematics",
          session_type: "practice",
          segment_plan: data.segment_plan,
        }),
      });
      router.push(`/session/${s.id}`);
    } catch {
      setStarting(false);
    }
  };

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <header className="mb-4">
        <h2 className="text-lg font-semibold">Today&apos;s Session · {data.total_minutes} min</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Complete these three activities to stay on track for your target grade.
        </p>
      </header>
      <ol className="space-y-3">
        {data.segment_plan.map((seg) => (
          <li key={seg.idx} className="flex items-start gap-3">
            <span
              className={`mt-1 grid h-5 w-5 place-items-center rounded-full text-[10px] ${
                seg.status === "done" || seg.status === "in_progress"
                  ? "bg-[var(--blue)] text-white"
                  : "border border-gray-300"
              }`}
            >
              {seg.status === "done" ? "✓" : seg.idx + 1}
            </span>
            <div>
              <div className="font-medium">
                {titleFor(seg)} · {seg.target_minutes} min
              </div>
              <div className="text-sm text-[var(--text-secondary)]">{seg.why}</div>
            </div>
          </li>
        ))}
      </ol>
      <button
        onClick={start}
        disabled={starting}
        className="mt-5 w-full rounded-lg bg-[var(--blue)] px-4 py-3 text-white disabled:opacity-50"
      >
        {starting ? "Starting…" : "Start session"}
      </button>
    </section>
  );
}
