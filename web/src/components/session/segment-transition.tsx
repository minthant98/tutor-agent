"use client";

import { Button } from "@/components/ui/button";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

export type SegmentIntent = "teach" | "reinforce" | "assess";

interface SegmentInfo {
  intent: SegmentIntent | string;
  topic?: string;
  minutes?: number;
}

interface SegmentTransitionProps {
  prev: SegmentInfo;
  next: SegmentInfo & { topic: string; minutes: number };
  onContinue: () => void;
}

function intentLabel(intent: string): string {
  switch (intent) {
    case "teach":
      return "Teach";
    case "reinforce":
      return "Reinforce";
    case "assess":
      return "Assess";
    default:
      // Capitalise unknown intents gracefully
      return intent.charAt(0).toUpperCase() + intent.slice(1);
  }
}

/**
 * SegmentTransition — full-viewport overlay shown between session segments.
 *
 * Design note: No minimum delay before Continue is clickable. The brief
 * originally suggested a 3-second minimum to ensure students register the
 * transition, but for MVP we allow immediate continuation. Students who
 * want to pause can simply wait. A mandatory delay adds friction without
 * clear benefit at this stage.
 *
 * Accessibility: role="dialog" aria-modal="true" so screen readers treat
 * this as a modal context and announce it on focus.
 */
export function SegmentTransition({
  prev,
  next,
  onContinue,
}: SegmentTransitionProps) {
  // ↵ triggers onContinue — ignoreInInput defaults true in the hook,
  // so typing in an input won't accidentally dismiss the overlay.
  useKeyboardShortcut("Enter", onContinue);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Segment complete"
      className="fixed inset-0 bg-[var(--surface-0)] flex items-center justify-center animate-in fade-in duration-300 ease-in-out z-50"
    >
      <div className="max-w-[440px] w-full px-6 text-center space-y-6">
        {/* Completed segment */}
        <div className="space-y-2">
          <div className="text-[14px] font-mono text-white/60 uppercase tracking-widest">
            Segment Complete ✓
          </div>
          <div className="text-[16px] text-white/80">
            {intentLabel(prev.intent)} finished.
          </div>
        </div>

        {/* Divider + next segment */}
        <div className="pt-8 border-t border-[var(--border-subtle)] space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-widest text-white/60">
            Next
          </div>
          <div className="text-[20px] font-sans text-white">
            {intentLabel(next.intent)} · {next.topic}
          </div>
          <div className="text-[12px] font-mono text-white/60">
            ≈ {next.minutes} minutes
          </div>
        </div>

        <Button variant="primary" onClick={onContinue}>
          Continue →
        </Button>
      </div>
    </div>
  );
}
