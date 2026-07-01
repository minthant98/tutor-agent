"use client";
import { ReactNode } from "react";
import { useRouter } from "next/navigation";

const STEPS = [
  "welcome",
  "education-system",
  "subjects",
  "exam-board",
  "exam-date",
  "target-grade",
  "assessment",
  "preferences",
  "roadmap",
] as const;
type Step = (typeof STEPS)[number];

export function WizardShell({
  step,
  children,
}: {
  step: Step;
  children: ReactNode;
}) {
  const router = useRouter();
  const idx = STEPS.indexOf(step);
  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      {/* Progress bar */}
      <div className="mb-6 flex items-center gap-2">
        {STEPS.map((s, i) => (
          <span
            key={s}
            className={`h-1.5 flex-1 rounded ${
              i <= idx ? "bg-[var(--blue)]" : "bg-gray-200"
            }`}
          />
        ))}
      </div>
      {/* Back button — hidden on welcome (0) and roadmap (last) */}
      {idx > 0 && idx < STEPS.length - 1 && (
        <button
          onClick={() => router.back()}
          className="mb-4 text-sm text-[var(--text-secondary)]"
        >
          ← Back
        </button>
      )}
      {children}
    </div>
  );
}
