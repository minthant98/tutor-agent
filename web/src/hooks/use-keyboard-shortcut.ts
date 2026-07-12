"use client";
import { useEffect } from "react";

type Options = { scope?: "global" | "session"; ignoreInInput?: boolean };

/**
 * useKeyboardShortcut — attach a keydown listener for a combo like:
 *   "Cmd+H", "Cmd+Shift+M", "Cmd+/", "?", "Enter", "Escape", " "
 *
 * - Cmd and Ctrl are treated as equivalent (metaKey || ctrlKey).
 * - By default, does NOT fire when the user is typing in an INPUT,
 *   TEXTAREA, or contentEditable element.
 */
export function useKeyboardShortcut(
  combo: string,
  handler: () => void,
  opts: Options = {}
) {
  const { ignoreInInput = true } = opts;

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (ignoreInInput && isTypingContext(e.target)) return;
      if (matches(e, combo)) {
        e.preventDefault();
        handler();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [combo, handler, ignoreInInput]);
}

function isTypingContext(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable;
}

function matches(e: KeyboardEvent, combo: string): boolean {
  const parts = combo.toLowerCase().split("+");
  const key = parts.pop()!;
  const wantMeta = parts.includes("cmd") || parts.includes("ctrl");
  const wantShift = parts.includes("shift");

  // Resolve key aliases
  const resolvedKey = key === " " ? " " : key;

  return (
    e.key.toLowerCase() === resolvedKey &&
    (!wantMeta || e.metaKey || e.ctrlKey) &&
    (!wantShift || e.shiftKey)
  );
}
