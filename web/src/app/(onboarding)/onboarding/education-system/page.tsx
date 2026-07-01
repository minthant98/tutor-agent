"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { SystemPicker } from "@/components/onboarding/fields/system-picker";

export default function EducationSystemStep() {
  const router = useRouter();
  const startTime = useRef<number>(0);
  const [system, setSystem] = useState<string>("");

  useEffect(() => {
    startTime.current = Date.now();
  }, []);

  const handleContinue = () => {
    // Education system is frontend-only — no backend endpoint.
    // A Levels is the only supported option; route directly to subjects.
    router.push("/onboarding/subjects");
  };

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
