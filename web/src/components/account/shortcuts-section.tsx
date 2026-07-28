"use client";

// Reuses the shortcut group data structure from ShortcutHelp (Task 6).
// Rendered as a persistent grouped table rather than a modal.

interface ShortcutRow {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  label: string;
  rows: ShortcutRow[];
}

const GROUPS: ShortcutGroup[] = [
  {
    label: "Global",
    rows: [
      { keys: ["?"], description: "Open keyboard shortcuts" },
      { keys: ["⌘K"], description: "Open command palette" },
      { keys: ["⌘H"], description: "Go to Home" },
      { keys: ["⌘P"], description: "Go to Practice" },
      { keys: ["⌘M"], description: "Go to Exam Marker" },
      { keys: ["⌘T"], description: "Go to Topics" },
      { keys: ["⌘G"], description: "Go to Progress" },
    ],
  },
  {
    label: "Session",
    rows: [
      { keys: ["⌘↵"], description: "Submit response" },
      { keys: ["⌘⇧M"], description: "Toggle microphone" },
      { keys: ["Esc"], description: "Dismiss / close overlay" },
    ],
  },
  {
    label: "Marker",
    rows: [
      { keys: ["⌘⇧U"], description: "Upload answer script" },
      { keys: ["⌘⇧S"], description: "Submit for marking" },
    ],
  },
  {
    label: "Alex",
    rows: [
      { keys: ["⌘/"], description: "Open Ask Alex drawer" },
      { keys: ["⌘⇧A"], description: "Toggle Alex sidebar" },
    ],
  },
  {
    label: "Cmd-K",
    rows: [
      { keys: ["⌘K"], description: "Toggle command palette" },
      { keys: ["↑ ↓"], description: "Navigate results" },
      { keys: ["↵"], description: "Select item" },
      { keys: ["Esc"], description: "Close palette" },
    ],
  },
];

function Key({ label }: { label: string }) {
  return (
    <kbd className="font-mono text-[11px] px-1.5 py-0.5 rounded-[var(--radius-input)] border border-[var(--border-subtle)] text-[var(--text-secondary)] bg-[var(--surface-2)] leading-none">
      {label}
    </kbd>
  );
}

export function ShortcutsSection() {
  return (
    <div className="space-y-8">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Keyboard Shortcuts
      </h2>

      {GROUPS.map((group) => (
        <section key={group.label}>
          <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">
            {group.label}
          </h3>
          <table className="w-full text-[13px]">
            <tbody>
              {group.rows.map((row) => (
                <tr
                  key={row.description}
                  className="border-b border-[var(--border-subtle)] last:border-0"
                >
                  <td className="py-1.5 pr-4 text-[var(--text-secondary)]">
                    {row.description}
                  </td>
                  <td className="py-1.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {row.keys.map((k) => (
                        <Key key={k} label={k} />
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
