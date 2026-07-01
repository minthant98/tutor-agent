"use client";
import { useState } from "react";

export function ExamDatePicker({
  initial = "",
  onChange,
}: {
  initial?: string;
  onChange: (date: string | null) => void;
}) {
  const [date, setDate] = useState<string>(initial);
  const [dontKnow, setDontKnow] = useState<boolean>(false);

  const handleDateChange = (val: string) => {
    setDate(val);
    onChange(val || null);
  };

  const handleDontKnow = (checked: boolean) => {
    setDontKnow(checked);
    if (checked) {
      onChange(null);
    } else {
      onChange(date || null);
    }
  };

  return (
    <div className="grid gap-4">
      <input
        type="date"
        value={date}
        disabled={dontKnow}
        min={new Date().toISOString().split("T")[0]}
        onChange={(e) => handleDateChange(e.target.value)}
        className={`w-full rounded-lg border border-[var(--border)] px-4 py-3 text-sm focus:outline-none focus:border-[var(--blue)] transition-colors
          ${dontKnow ? "cursor-not-allowed opacity-50" : ""}`}
      />
      <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
        <input
          type="checkbox"
          checked={dontKnow}
          onChange={(e) => handleDontKnow(e.target.checked)}
          className="h-4 w-4 rounded border-[var(--border)] accent-[var(--blue)]"
        />
        Don&apos;t know yet
      </label>
    </div>
  );
}
