"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { ExamDatePicker } from "@/components/onboarding/fields/exam-date-picker";
import { onboardingApi } from "@/lib/api/onboarding";

export default function ExamDateStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [date, setDate] = useState<string | null>(null);
  const [canContinue, setCanContinue] = useState<boolean>(false);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleChange = (val: string | null) => {
    setDate(val);
    // Can continue if they have a date OR if they explicitly chose null (don't know)
    // We use a separate flag tracked via the picker's dontKnow checkbox
    setCanContinue(true);
  };

  return (
    <WizardShell step="exam-date">
      <h1 className="mb-2 text-2xl font-semibold">When&apos;s your exam?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        We&apos;ll count down and help you prepare in time.
      </p>
      <ExamDatePicker onChange={handleChange} />
      <button
        disabled={!canContinue}
        onClick={async () => {
          await onboardingApi.submitExamDate({ exam_date: date });
          try {
            posthog.capture("onboarding_step_completed", {
              step_name: "exam-date",
              time_on_step_sec: Math.round((Date.now() - startTime.current) / 1000),
            });
          } catch (_) {}
          const state = await onboardingApi.getState();
          router.push(`/onboarding/${state.next_step}`);
        }}
        className="mt-8 rounded-lg bg-[var(--blue)] px-5 py-3 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </WizardShell>
  );
}
