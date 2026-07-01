"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { SubjectPicker } from "@/components/onboarding/fields/subject-picker";
import { onboardingApi } from "@/lib/api/onboarding";

export default function SubjectsStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [subjects, setSubjects] = useState<string[]>([]);

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  return (
    <WizardShell step="subjects">
      <h1 className="mb-2 text-2xl font-semibold">Which subjects?</h1>
      <p className="mb-6 text-[var(--text-secondary)]">
        Pick the subjects you&apos;re studying.
      </p>
      <SubjectPicker onChange={setSubjects} />
      <button
        disabled={subjects.length === 0}
        onClick={async () => {
          await onboardingApi.submitSubjects({ subjects });
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
