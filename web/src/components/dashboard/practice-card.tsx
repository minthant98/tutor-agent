"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api/practice";
import { QuickPracticeModal } from "./quick-practice-modal";

interface Props {
  subject: string;
}

export function PracticeCard({ subject }: Props) {
  const router = useRouter();
  const [showQuick, setShowQuick] = useState(false);
  const [weakStarting, setWeakStarting] = useState(false);

  const startWeakAreas = async () => {
    setWeakStarting(true);
    try {
      const s = await practiceApi.startWeakAreas(subject);
      router.push(`/session/${s.session_id}`);
    } catch {
      setWeakStarting(false);
      // TODO: surface toast — see design notes
    }
  };

  return (
    <section className="rounded-lg border border-[var(--border)] bg-white p-5">
      <header className="mb-3">
        <h2 className="text-lg font-semibold">Practice</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Focused reps between daily sessions.
        </p>
      </header>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setShowQuick(true)}
          className="rounded-lg bg-[var(--blue)] px-4 py-2 text-white"
        >
          Quick Practice
        </button>
        <button
          onClick={startWeakAreas}
          disabled={weakStarting}
          className="rounded-lg border border-[var(--blue)] bg-blue-50 px-4 py-2 text-[var(--blue)] disabled:opacity-50"
        >
          {weakStarting ? "Starting…" : "Practice Weak Areas"}
        </button>
      </div>
      <p className="mt-3 text-xs text-[var(--text-secondary)]">
        Or tap a weak topic below to drill in.
      </p>

      {showQuick && (
        <QuickPracticeModal subject={subject} onClose={() => setShowQuick(false)} />
      )}
    </section>
  );
}
