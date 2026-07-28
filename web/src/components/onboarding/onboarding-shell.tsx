"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut";

const TOTAL_STEPS = 6;

interface OnboardingShellProps {
  /** Zero-based step index (0–5). */
  currentStep: number;
  /** Alex framing line shown above the step heading. */
  alexLine: string;
  /** Step field content. */
  children: ReactNode;
  /** Heading for the step (passed separately so Shell can render it). */
  heading?: string;
  /** Called when Continue is clicked. */
  onContinue?: () => void;
  /** When false, Continue button is disabled. Defaults to true. */
  canContinue?: boolean;
  /** When true, shows a loading state on Continue. */
  continuing?: boolean;
}

/**
 * OnboardingShell — 6-step wizard wrapper.
 *
 * Layout:
 *   56px sticky top progress rail (6 dots)
 *   Centered content area (max-w-[560px], pt-24 px-6)
 *     Alex framing line (border-l-2 border-readiness-2 pl-3)
 *     heading (if provided)
 *     children (the step field)
 *   Sticky bottom bar: Back (ghost, hidden on step 0) + Continue (primary)
 */
export function OnboardingShell({
  currentStep,
  alexLine,
  children,
  heading,
  onContinue,
  canContinue = true,
  continuing = false,
}: OnboardingShellProps) {
  const router = useRouter();

  // ↵ submits when Continue is enabled
  useKeyboardShortcut("Enter", () => {
    if (canContinue && onContinue) onContinue();
  });

  return (
    <div className="min-h-screen flex flex-col bg-[var(--surface-0)]">
      {/* ── Progress rail (56px sticky) ── */}
      <div
        className={cn(
          "sticky top-0 z-10 h-14 border-b border-[var(--border-subtle)]",
          "bg-[var(--surface-0)] flex items-center justify-center"
        )}
        aria-label="Onboarding progress"
      >
        <ol role="list" className="flex items-center gap-3">
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => {
            const isCompleted = i < currentStep;
            const isCurrent = i === currentStep;
            const isUpcoming = i > currentStep;
            return (
              <li
                key={i}
                role="listitem"
                aria-current={isCurrent ? "step" : undefined}
                aria-label={`Step ${i + 1}${isCurrent ? " (current)" : isCompleted ? " (completed)" : ""}`}
                className={cn(
                  "w-2.5 h-2.5 rounded-full transition-all duration-fast ease-standard",
                  isCompleted && "bg-[var(--text-muted)]",
                  isCurrent && "bg-[var(--primary)]",
                  isUpcoming && "border border-[var(--border-subtle)] bg-transparent"
                )}
              />
            );
          })}
        </ol>
      </div>

      {/* ── Centered content ── */}
      <div className="flex-1 flex flex-col items-center px-6 pt-24 pb-32">
        <div className="w-full max-w-[560px]">
          {/* Alex framing line */}
          <p className="mb-6 border-l-2 border-[var(--readiness-2)] pl-3 font-sans text-[14px] text-[var(--text-secondary)]">
            {alexLine}
          </p>

          {/* Step heading */}
          {heading && (
            <h1 className="mb-8 text-[24px] font-semibold text-[var(--text-primary)]">
              {heading}
            </h1>
          )}

          {/* Field content */}
          {children}
        </div>
      </div>

      {/* ── Sticky bottom bar ── */}
      <div
        className={cn(
          "sticky bottom-0 z-10 border-t border-[var(--border-subtle)]",
          "bg-[var(--surface-0)] px-6 py-4",
          "flex items-center justify-between"
        )}
      >
        {currentStep > 0 ? (
          <Button variant="ghost" onClick={() => router.back()}>
            Back
          </Button>
        ) : (
          <span />
        )}

        <Button
          variant="primary"
          onClick={onContinue}
          disabled={!canContinue || continuing}
        >
          {continuing ? "Saving..." : "Continue"}
        </Button>
      </div>
    </div>
  );
}
