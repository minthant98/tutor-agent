const SUBJECT_LABELS: Record<string, string> = {
  pure_mathematics: "Pure Mathematics",
  mechanics_statistics: "Mechanics & Statistics",
  physics: "Physics",
  chemistry: "Chemistry",
};

interface SubjectSwitcherProps {
  current: string;
  options: string[];
  onChange: (subject: string) => void;
}

export function SubjectSwitcher({ current, options, onChange }: SubjectSwitcherProps) {
  if (options.length < 2) return null;

  return (
    <select
      value={current}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--blue)]"
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {SUBJECT_LABELS[opt] ?? opt.replace(/_/g, " ")}
        </option>
      ))}
    </select>
  );
}
