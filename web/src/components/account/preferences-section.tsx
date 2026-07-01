"use client";
import { useState } from "react";
import { accountApi } from "@/lib/api/account";
import type { PreferencesOut } from "@/lib/types";

const PREFS: { key: keyof PreferencesOut; label: string }[] = [
  { key: "worked_examples", label: "Worked examples" },
  { key: "visual", label: "Visual explanations" },
  { key: "step_by_step", label: "Step-by-step explanations" },
  { key: "practice", label: "Practice questions" },
];

export function PreferencesSection({ initial }: { initial: PreferencesOut }) {
  const [state, setState] = useState<PreferencesOut>(initial);

  const toggle = async (key: keyof PreferencesOut) => {
    const next: PreferencesOut = { ...state, [key]: !state[key] };
    setState(next);
    await accountApi.patchPreferences(next);
  };

  return (
    <div className="grid gap-2">
      {PREFS.map((p) => (
        <label
          key={p.key}
          className="flex cursor-pointer items-center gap-3 rounded-md border border-[var(--border)] bg-white p-3"
        >
          <input
            type="checkbox"
            checked={!!state[p.key]}
            onChange={() => toggle(p.key)}
          />
          <span>{p.label}</span>
        </label>
      ))}
    </div>
  );
}
