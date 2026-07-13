"use client";

import { useState, useEffect, useCallback } from "react";
import { AssessBlock, type AssessQuestion } from "./assess-block";

export type ReinforceStep = {
  id: string;
  text: string;
};

interface ReinforceBlockProps {
  steps: ReinforceStep[];
  followUp?: AssessQuestion;
}

/**
 * ReinforceBlock — worked example step-through, keyboard-driven.
 *
 * Reveals steps one at a time. Space advances to the next step.
 * After all steps are revealed, an optional followUp AssessBlock appears.
 *
 * Uses a simple show-up-to-index approach (no Accordion) to keep the
 * reveal behaviour predictable and testable.
 */
export function ReinforceBlock({ steps, followUp }: ReinforceBlockProps) {
  // Index of the highest step revealed. Starts at 0 (first step visible).
  const [revealedUpTo, setRevealedUpTo] = useState(0);

  const allRevealed = revealedUpTo >= steps.length - 1;
  const showFollowUp = allRevealed && followUp !== undefined;

  const advanceStep = useCallback(() => {
    setRevealedUpTo((prev) => {
      if (prev < steps.length - 1) return prev + 1;
      return prev; // already at last step
    });
  }, [steps.length]);

  // Space key listener — only active in reinforce mode
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.code === "Space" && !allRevealed) {
        // Only intercept when not focused on an input/textarea
        const tag = (e.target as HTMLElement).tagName;
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        e.preventDefault();
        advanceStep();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [advanceStep, allRevealed]);

  return (
    <div className="max-w-[800px] mx-auto py-16 space-y-6">
      {steps.slice(0, revealedUpTo + 1).map((step, i) => (
        <div
          key={step.id}
          className="border border-[var(--border-subtle)] rounded-lg p-5 bg-[var(--surface-1)]"
        >
          <p className="text-[12px] font-mono text-[var(--text-secondary)] mb-2">
            Step {i + 1}
          </p>
          <p className="text-[16px] font-sans leading-[1.6] text-[var(--text-primary)]">
            {step.text}
          </p>
        </div>
      ))}

      {/* Advance hint — hide once all steps revealed */}
      {!allRevealed && (
        <p className="text-[13px] text-[var(--text-secondary)] text-center">
          Press{" "}
          <kbd className="px-1.5 py-0.5 rounded border border-[var(--border-subtle)] font-mono text-[12px]">
            Space
          </kbd>{" "}
          to reveal next step
        </p>
      )}

      {/* Optional follow-up question rendered as AssessBlock */}
      {showFollowUp && <AssessBlock question={followUp!} />}
    </div>
  );
}
