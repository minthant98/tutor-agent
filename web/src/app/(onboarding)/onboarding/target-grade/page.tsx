"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { OnboardingShell } from "@/components/onboarding/onboarding-shell";
import { GradePicker } from "@/components/onboarding/fields/grade-picker";
import { onboardingApi } from "@/lib/api/onboarding";
import { useFeatureFlag } from "@/lib/feature-flags";

export default function TargetGradeStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [grade, setGrade] = useState<string>("");
  const [continuing, setContinuing] = useState(false);
  const v3 = useFeatureFlag("onboarding_v3", false);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleContinue = async () => {
    setContinuing(true);
    try {
      await onboardingApi.submitTargetGrade({ target_grade: grade });
      try {
        posthog.capture("onboarding_step_completed", {
          step_name: "target-grade",
          time_on_step_sec: Math.round((Date.now() - startTime.current) / 1000),
        });
      } catch (_) {}
      const state = await onboardingApi.getState();
      // After target-grade, backend next_step = "preferences"
      // But our wizard has "assessment" before "preferences"
      // Map: if next_step is "preferences", route to assessment first
      const next = state.next_step === "preferences" ? "assessment" : state.next_step;
      router.push(`/onboarding/${next}`);
    } finally {
      setContinuing(false);
    }
  };

  if (v3) {
    return (
      <OnboardingShell
        currentStep={4}
        alexLine="Readiness is measured against this. You can raise or lower it later."
        heading="What is your target grade?"
        onContinue={handleContinue}
        canContinue={!!grade}
        continuing={continuing}
      >
        <GradePicker onChange={setGrade} />
      </OnboardingShell>
    );
  }

  return (
    <WizardShell step="target-grade">
      <h1 className="mb-2 text-2xl font-semibold">What&apos;s your target grade?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        Alex will calibrate your study plan to get you there.
      </p>
      <GradePicker onChange={setGrade} />
      <button
        disabled={!grade}
        onClick={handleContinue}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </WizardShell>
  );
}
