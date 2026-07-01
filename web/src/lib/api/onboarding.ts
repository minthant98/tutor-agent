import { apiFetch } from "@/lib/api";
import type {
  WizardStateOut,
  SubjectsIn,
  ExamBoardIn,
  ExamDateIn,
  TargetGradeIn,
  WizardPreferencesIn,
} from "@/lib/types";

export const onboardingApi = {
  getState: (): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/state"),

  submitSubjects: (body: SubjectsIn): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/subjects", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitExamBoard: (body: ExamBoardIn): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/exam-board", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitExamDate: (body: ExamDateIn): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/exam-date", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitTargetGrade: (body: TargetGradeIn): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/target-grade", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitPreferences: (body: WizardPreferencesIn): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/preferences", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  finalize: (): Promise<WizardStateOut> =>
    apiFetch<WizardStateOut>("/onboarding/complete", { method: "POST" }),
};
