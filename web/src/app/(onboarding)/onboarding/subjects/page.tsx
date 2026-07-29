"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { OnboardingShell } from "@/components/onboarding/onboarding-shell";
import { SubjectPicker } from "@/components/onboarding/fields/subject-picker";
import { onboardingApi } from "@/lib/api/onboarding";
import { useFeatureFlag } from "@/lib/feature-flags";

export default function SubjectsStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [continuing, setContinuing] = useState(false);
  const v3 = useFeatureFlag("onboarding_v3", true);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleContinue = async () => {
    setContinuing(true);
    try {
      await onboardingApi.submitSubjects({ subjects });
      try {
        posthog.capture("onboarding_step_completed", {
          step_name: "subjects",
          time_on_step_sec: Math.round((Date.now() - startTime.current) / 1000),
        });
      } catch (_) {}
      const state = await onboardingApi.getState();
      router.push(`/onboarding/${state.next_step}`);
    } finally {
      setContinuing(false);
    }
  };

  if (v3) {
    return (
      <OnboardingShell
        currentStep={1}
        alexLine="You can add more later — but a first subject lets Alex build your initial roadmap."
        heading="Which subjects?"
        onContinue={handleContinue}
        canContinue={subjects.length > 0}
        continuing={continuing}
      >
        <SubjectPicker onChange={setSubjects} />
      </OnboardingShell>
    );
  }

  return (
    <WizardShell step="subjects">
      <h1 className="mb-2 text-2xl font-semibold">Which subjects?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        Pick the subjects you&apos;re studying.
      </p>
      <SubjectPicker onChange={setSubjects} />
      <button
        disabled={subjects.length === 0}
        onClick={handleContinue}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </WizardShell>
  );
}
