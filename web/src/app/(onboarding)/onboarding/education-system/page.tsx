"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { OnboardingShell } from "@/components/onboarding/onboarding-shell";
import { SystemPicker } from "@/components/onboarding/fields/system-picker";
import { useFeatureFlag } from "@/lib/feature-flags";

export default function EducationSystemStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [system, setSystem] = useState<string>("");
  const v3 = useFeatureFlag("onboarding_v3", false);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleContinue = () => {
    // Education system is frontend-only — no backend endpoint.
    // A Levels is the only supported option; route directly to subjects.
    try {
      posthog.capture("onboarding_step_completed", {
        step_name: "education-system",
        time_on_step_sec: Math.round((Date.now() - startTime.current) / 1000),
      });
    } catch (_) {}
    router.push("/onboarding/subjects");
  };

  if (v3) {
    return (
      <OnboardingShell
        currentStep={0}
        alexLine="Alex needs to know your syllabus before it can plan sessions."
        heading="What education system are you in?"
        onContinue={handleContinue}
        canContinue={system === "a_level"}
      >
        <SystemPicker onChange={setSystem} />
      </OnboardingShell>
    );
  }

  return (
    <WizardShell step="education-system">
      <h1 className="mb-2 text-2xl font-semibold">
        What education system are you in?
      </h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        We&apos;ll tailor the content and syllabus for you.
      </p>
      <SystemPicker onChange={setSystem} />
      <button
        disabled={system !== "a_level"}
        onClick={handleContinue}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </WizardShell>
  );
}
