"use client";
import Link from "next/link";
import { WizardShell } from "@/components/onboarding/wizard-shell";

export default function WelcomePage() {
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
        className="inline-block rounded-lg bg-[var(--blue)] px-5 py-3 text-white"
      >
        Get started
      </Link>
    </WizardShell>
  );
}
