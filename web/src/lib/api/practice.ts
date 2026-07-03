import { apiFetch } from "@/lib/api";
import type { PracticeTopic, StartSessionResponse } from "@/lib/types";

export const practiceApi = {
  getTopics: (subject: string) =>
    apiFetch<PracticeTopic[]>(`/practice/topics?subject=${encodeURIComponent(subject)}`),
  startQuick: (subject: string, topic: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "quick_practice", topic }),
    }),
  startWeakAreas: (subject: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "weak_areas" }),
    }),
  startDrillIn: (subject: string, topic: string) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ subject, session_type: "drill_in", topic }),
    }),
};
