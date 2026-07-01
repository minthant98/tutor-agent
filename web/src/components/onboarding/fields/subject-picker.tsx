"use client";
import { useState } from "react";

const SUBJECTS = [
  { id: "pure_mathematics", label: "Pure Mathematics", supported: true },
  {
    id: "mechanics_statistics",
    label: "Mechanics & Statistics",
    supported: false,
  },
  { id: "physics", label: "Physics", supported: false },
  { id: "chemistry", label: "Chemistry", supported: false },
];

export function SubjectPicker({
  initial = [],
  onChange,
}: {
  initial?: string[];
  onChange: (s: string[]) => void;
}) {
  const [selected, setSelected] = useState<string[]>(initial);

  const toggle = (id: string) => {
    const next = selected.includes(id)
      ? selected.filter((s) => s !== id)
      : [...selected, id];
    setSelected(next);
    onChange(next);
  };

  return (
    <div className="grid gap-2">
      {SUBJECTS.map((s) => (
        <button
          key={s.id}
          disabled={!s.supported}
          onClick={() => toggle(s.id)}
          title={!s.supported ? "Coming soon" : undefined}
          className={`flex items-center justify-between rounded-lg border p-3 text-left
            ${
              selected.includes(s.id)
                ? "border-[var(--blue)] bg-blue-50"
                : "border-[var(--border)]"
            }
            ${
              !s.supported
                ? "cursor-not-allowed opacity-50"
                : "hover:border-[var(--blue)]"
            }`}
        >
          <span>{s.label}</span>
          {!s.supported && (
            <span className="text-xs text-[var(--text-secondary)]">
              Coming soon
            </span>
          )}
          {s.supported && selected.includes(s.id) && (
            <span className="text-[var(--blue)]">✓</span>
          )}
        </button>
      ))}
    </div>
  );
}
