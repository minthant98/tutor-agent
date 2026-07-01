"use client";
import { useEffect, useRef } from "react";
import Link from "next/link";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";

export default function WelcomePage() {
  const startTime = useRef<number>(0);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleClick = () => {
    try {
      posthog.capture("onboarding_step_completed", {
        step_name: "welcome",
        time_on_step_sec: Math.round((Date.now() - startTime.current) / 1000),
      });
    } catch (_) {}
  };

  return (
    <WizardShell step="welcome">
      <h1 className="mb-3 text-3xl font-semibold">
        Meet Alex, your AI exam coach.
      </h1>
      <p className="mb-8 text-[var(--text-secondary)]">
        Stride will create a personalised study plan based on your subjects,
        goals, and current ability.
      </p>
      <Link
        href="/onboarding/education-system"
        onClick={handleClick}
        className="inline-block rounded-lg bg-[var(--blue)] px-5 py-3 text-white"
      >
        Get started
      </Link>
    </WizardShell>
  );
}
