"use client";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

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

/** Renders a single keyboard key in a <kbd> element styled per Stride design tokens. */
function Key({ label }: { label: string }) {
  return (
    <kbd className="font-mono text-[11px] px-1.5 py-0.5 rounded-[var(--radius-input)] border border-[var(--border-subtle)] text-[var(--text-secondary)] bg-[var(--surface-2)] leading-none">
      {label}
    </kbd>
  );
}

/**
 * ShortcutHelp — opens on `?` via useKeyboardShortcut.
 * Renders grouped tables of keyboard bindings.
 */
export function ShortcutHelp() {
  const [open, setOpen] = useState(false);

  useKeyboardShortcut("?", () => setOpen(true));

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        aria-label="Keyboard shortcuts"
        className="max-w-[540px] max-h-[80vh] overflow-y-auto"
      >
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
        </DialogHeader>

        <div className="mt-4 flex flex-col gap-6">
          {GROUPS.map((group) => (
            <section key={group.label}>
              <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">
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
      </DialogContent>
    </Dialog>
  );
}
