"use client";
import { useState } from "react";

const SYSTEMS = [
  { id: "a_level", label: "A Levels", supported: true },
  { id: "gcse", label: "GCSE", supported: false },
  { id: "ib", label: "International Baccalaureate (IB)", supported: false },
  { id: "university", label: "University", supported: false },
];

export function SystemPicker({
  initial = "",
  onChange,
}: {
  initial?: string;
  onChange: (s: string) => void;
}) {
  const [selected, setSelected] = useState<string>(initial);

  const pick = (id: string) => {
    setSelected(id);
    onChange(id);
  };

  return (
    <div className="grid gap-2">
      {SYSTEMS.map((s) => (
        <button
          key={s.id}
          disabled={!s.supported}
          onClick={() => pick(s.id)}
          title={!s.supported ? "Coming soon" : undefined}
          className={`flex items-center justify-between rounded-lg border p-3 text-left
            ${
              selected === s.id
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
          {s.supported && selected === s.id && (
            <span className="text-[var(--blue)]">✓</span>
          )}
        </button>
      ))}
    </div>
  );
}
