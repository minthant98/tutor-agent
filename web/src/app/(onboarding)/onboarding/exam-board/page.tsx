"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { OnboardingShell } from "@/components/onboarding/onboarding-shell";
import { BoardPicker } from "@/components/onboarding/fields/board-picker";
import { onboardingApi } from "@/lib/api/onboarding";
import { useFeatureFlag } from "@/lib/feature-flags";

export default function ExamBoardStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [board, setBoard] = useState<string>("");
  const [continuing, setContinuing] = useState(false);
  const v3 = useFeatureFlag("onboarding_v3", false);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleContinue = async () => {
    setContinuing(true);
    try {
      await onboardingApi.submitExamBoard({ exam_board: board });
      try {
        posthog.capture("onboarding_step_completed", {
          step_name: "exam-board",
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
        currentStep={2}
        alexLine="This decides which past papers Alex uses."
        heading="Which exam board?"
        onContinue={handleContinue}
        canContinue={!!board}
        continuing={continuing}
      >
        <BoardPicker onChange={setBoard} />
      </OnboardingShell>
    );
  }

  return (
    <WizardShell step="exam-board">
      <h1 className="mb-2 text-2xl font-semibold">Which exam board?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        We&apos;ll use the right syllabus and mark schemes.
      </p>
      <BoardPicker onChange={setBoard} />
      <button
        disabled={!board}
        onClick={handleContinue}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </WizardShell>
  );
}
