"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export interface OnboardingCompletePlan {
  minutes: number;
  segments: number;
  /** Optional session route to navigate to. Defaults to /sessions/today. */
  sessionHref?: string;
}

interface OnboardingCompleteProps {
  plan: OnboardingCompletePlan;
}

/**
 * OnboardingComplete — exit surface after the 6-step wizard.
 *
 * Renders:
 *   Alex framing line
 *   "You're set." heading
 *   Plan meta: "Today's plan · N minutes · N segments"
 *   "Go to today's session" CTA
 *
 * No celebratory copy. No exclamation marks. No emoji.
 */
export function OnboardingComplete({ plan }: OnboardingCompleteProps) {
  const router = useRouter();
  const href = plan.sessionHref ?? "/sessions/today";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-[var(--surface-0)]">
      <div className="w-full max-w-[560px]">
        {/* Alex framing */}
        <p className="mb-8 border-l-2 border-[var(--readiness-2)] pl-3 font-sans text-[14px] text-[var(--text-secondary)]">
          Your roadmap is ready. Alex generated a session plan for today based on your baseline.
        </p>

        {/* Heading */}
        <h1 className="mb-6 text-[32px] font-semibold text-[var(--text-primary)]">
          You&apos;re set.
        </h1>

        {/* Plan meta */}
        <p className="mb-10 text-[14px] text-[var(--text-secondary)]">
          Today&apos;s plan · {plan.minutes} minutes · {plan.segments} segments
        </p>

        {/* CTA */}
        <Button
          variant="primary"
          size="lg"
          onClick={() => router.push(href)}
        >
          Go to today&apos;s session
        </Button>
      </div>
    </div>
  );
}
