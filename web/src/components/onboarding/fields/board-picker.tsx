"use client";
import { useState } from "react";

const BOARDS = [
  { id: "edexcel", label: "Edexcel", supported: true },
  { id: "cambridge", label: "Cambridge (CIE)", supported: true },
  { id: "aqa", label: "AQA", supported: false },
  { id: "ocr", label: "OCR", supported: false },
];

export function BoardPicker({
  initial = "",
  onChange,
}: {
  initial?: string;
  onChange: (b: string) => void;
}) {
  const [selected, setSelected] = useState<string>(initial);

  const pick = (id: string) => {
    setSelected(id);
    onChange(id);
  };

  return (
    <div className="grid gap-2">
      {BOARDS.map((b) => (
        <button
          key={b.id}
          disabled={!b.supported}
          onClick={() => pick(b.id)}
          title={!b.supported ? "Coming soon" : undefined}
          className={`flex items-center justify-between rounded-lg border p-3 text-left
            ${
              selected === b.id
                ? "border-[var(--blue)] bg-blue-50"
                : "border-[var(--border)]"
            }
            ${
              !b.supported
                ? "cursor-not-allowed opacity-50"
                : "hover:border-[var(--blue)]"
            }`}
        >
          <span>{b.label}</span>
          {!b.supported && (
            <span className="text-xs text-[var(--text-secondary)]">
              Coming soon
            </span>
          )}
          {b.supported && selected === b.id && (
            <span className="text-[var(--blue)]">✓</span>
          )}
        </button>
      ))}
    </div>
  );
}
