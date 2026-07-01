"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { onboardingApi } from "@/lib/api/onboarding";

const PREFERENCE_OPTIONS = [
  {
    id: "worked_examples",
    label: "Worked examples",
    desc: "See fully worked solutions alongside problems",
  },
  {
    id: "visual",
    label: "Visual explanations",
    desc: "Diagrams and graphs wherever possible",
  },
  {
    id: "step_by_step",
    label: "Step-by-step guidance",
    desc: "Break every solution into small steps",
  },
  {
    id: "practice",
    label: "Lots of practice",
    desc: "More exam-style questions, less theory",
  },
];

type PrefKey = "worked_examples" | "visual" | "step_by_step" | "practice";

export default function PreferencesStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [prefs, setPrefs] = useState<Record<PrefKey, boolean>>({
    worked_examples: false,
    visual: false,
    step_by_step: false,
    practice: false,
  });

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const toggle = (key: PrefKey) =>
    setPrefs((p) => ({ ...p, [key]: !p[key] }));

  return (
    <WizardShell step="preferences">
      <h1 className="mb-2 text-2xl font-semibold">How do you like to learn?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        Choose as many as you like — you can change these anytime.
      </p>
      <div className="grid gap-2">
        {PREFERENCE_OPTIONS.map((opt) => {
          const key = opt.id as PrefKey;
          const active = prefs[key];
          return (
            <button
              key={opt.id}
              onClick={() => toggle(key)}
              className={`flex items-center justify-between rounded-lg border p-3 text-left transition-colors
                ${
                  active
                    ? "border-[var(--blue)] bg-blue-50"
                    : "border-[var(--border)] hover:border-[var(--blue)]"
                }`}
            >
              <div>
                <div className="font-medium">{opt.label}</div>
                <div className="text-sm text-[var(--text-secondary)]">
                  {opt.desc}
                </div>
              </div>
              {active && <span className="text-[var(--blue)]">✓</span>}
            </button>
          );
        })}
      </div>
      <button
        onClick={async () => {
          await onboardingApi.submitPreferences(prefs);
          const state = await onboardingApi.getState();
          router.push(`/onboarding/${state.next_step}`);
        }}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white"
      >
        Continue
      </button>
    </WizardShell>
  );
}
