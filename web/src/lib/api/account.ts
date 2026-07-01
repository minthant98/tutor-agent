import { apiFetch } from "@/lib/api";
import type { AccountOut, SubjectPatch, PreferencesOut, ProfilePatch } from "@/lib/types";

export const accountApi = {
  get: (): Promise<AccountOut> =>
    apiFetch<AccountOut>("/account"),

  patchSubject: (subjectId: string, body: SubjectPatch): Promise<AccountOut> =>
    apiFetch<AccountOut>(`/account/subjects/${subjectId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  patchPreferences: (body: Partial<PreferencesOut>): Promise<AccountOut> =>
    apiFetch<AccountOut>("/account/preferences", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  patchProfile: (body: ProfilePatch): Promise<AccountOut> =>
    apiFetch<AccountOut>("/account/profile", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
};
