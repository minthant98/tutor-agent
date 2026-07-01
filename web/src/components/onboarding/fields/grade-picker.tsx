"use client";
import { useState } from "react";

const GRADES = [
  { id: "A*", label: "A*", supported: true },
  { id: "A", label: "A", supported: true },
  { id: "B", label: "B", supported: true },
  { id: "C", label: "C", supported: true },
  { id: "D", label: "D", supported: true },
  { id: "E", label: "E", supported: true },
];

export function GradePicker({
  initial = "",
  onChange,
}: {
  initial?: string;
  onChange: (g: string) => void;
}) {
  const [selected, setSelected] = useState<string>(initial);

  const pick = (id: string) => {
    setSelected(id);
    onChange(id);
  };

  return (
    <div className="grid gap-2">
      <select
        value={selected}
        onChange={(e) => pick(e.target.value)}
        className="w-full rounded-lg border border-[var(--border)] px-4 py-3 text-sm focus:outline-none focus:border-[var(--blue)] transition-colors bg-white"
      >
        <option value="" disabled>
          Select target grade
        </option>
        {GRADES.map((g) => (
          <option key={g.id} value={g.id}>
            {g.label}
          </option>
        ))}
      </select>
    </div>
  );
}
