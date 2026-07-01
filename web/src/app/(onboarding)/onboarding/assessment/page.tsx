"use client";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/onboarding/wizard-shell";
import { apiFetch } from "@/lib/api";
import { onboardingApi } from "@/lib/api/onboarding";

export default function AssessmentStep() {
  const router = useRouter();

  const skip = async () => {
    const s = await onboardingApi.getState();
    router.push(`/onboarding/${s.next_step}`);
  };

  const takeDiagnostic = async () => {
    const session = await apiFetch<{ session_id: string }>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({
        subject: "pure_mathematics",
        session_type: "diagnostic",
        return_to: "/onboarding/preferences",
      }),
    });
    router.push(`/session/${session.session_id}`);
  };

  return (
    <WizardShell step="assessment">
      <h1 className="mb-6 text-2xl font-semibold">Let&apos;s get a baseline.</h1>
      <div className="grid gap-3">
        <button
          onClick={takeDiagnostic}
          className="rounded-lg border border-[var(--blue)] bg-blue-50 p-4 text-left"
        >
          <div className="font-semibold">Take a 10-minute diagnostic</div>
          <div className="text-sm text-[var(--text-secondary)]">
            Recommended — gives Alex a real picture of where you are.
          </div>
        </button>
        <button
          onClick={skip}
          className="rounded-lg border border-[var(--border)] p-4 text-left"
        >
          <div className="font-semibold">Skip for now</div>
          <div className="text-sm text-[var(--text-secondary)]">
            Alex will calibrate during your first session.
          </div>
        </button>
      </div>
    </WizardShell>
  );
}
