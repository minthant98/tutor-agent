"use client";

/**
 * RevisionModeToggle — Radix Switch in the topics landing header.
 *
 * State is persisted to sessionStorage under key "stride:topics-revision-mode"
 * so it survives page navigations within the same tab but resets on new sessions.
 *
 * When enabled:
 *   - Hides "Not started" topics
 *   - Shows only "Needs review" + "Practising" + "Mastered" topics
 *   - Sorts by mastery ascending (low mastery = highest urgency)
 *
 * Usage:
 *   <RevisionModeToggle value={revisionMode} onChange={setRevisionMode} />
 */

import { Switch } from "@/components/ui/switch";

export const REVISION_MODE_KEY = "stride:topics-revision-mode";

interface RevisionModeToggleProps {
  value: boolean;
  onChange: (v: boolean) => void;
}

export function RevisionModeToggle({ value, onChange }: RevisionModeToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="revision-mode" className="text-[14px] font-sans text-[var(--text-secondary)] select-none cursor-pointer">
        Revision mode
      </label>
      <Switch
        id="revision-mode"
        checked={value}
        onCheckedChange={onChange}
        aria-label="Toggle revision mode"
      />
    </div>
  );
}

/**
 * Read initial revision mode value from sessionStorage.
 * Safe to call in useEffect (after mount) — not during SSR.
 */
export function readRevisionMode(): boolean {
  try {
    return sessionStorage.getItem(REVISION_MODE_KEY) === "true";
  } catch {
    return false;
  }
}

/**
 * Persist revision mode value to sessionStorage.
 */
export function writeRevisionMode(value: boolean): void {
  try {
    sessionStorage.setItem(REVISION_MODE_KEY, value ? "true" : "false");
  } catch {
    // sessionStorage not available (e.g. private browsing with storage blocked)
  }
}
