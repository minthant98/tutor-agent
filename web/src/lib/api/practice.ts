import { apiFetch } from "@/lib/api";
import type { PracticeTopic, StartSessionResponse } from "@/lib/types";

export interface WeakTopicItem {
  id: string;
  label: string;
}

export interface PracticeLandingData {
  narration: string;
  weak_topics: WeakTopicItem[];
}

export interface PlanSegment {
  intent: string;
  topic: string;
}

export interface PracticePlanData {
  narration: string;
  segments: PlanSegment[];
  minutes: number;
}

export interface DrillResumeData {
  session_id: string;
  topic_label: string;
  progress: { current: number; total: number };
}

export const practiceApi = {
  getTopics: (subject: string) =>
    apiFetch<PracticeTopic[]>(`/practice/topics?subject=${encodeURIComponent(subject)}`),

  getLandingV3: (subject: string) =>
    apiFetch<PracticeLandingData>(`/practice/v3/landing?subject=${encodeURIComponent(subject)}`),

  getPlan: (mode: string, topic?: string | null, skill?: string | null) => {
    const params = new URLSearchParams({ mode });
    if (topic) params.set("topic", topic);
    if (skill) params.set("skill", skill);
    return apiFetch<PracticePlanData>(`/practice/plan?${params.toString()}`);
  },

  getDrillResume: (topic: string) =>
    apiFetch<DrillResumeData | null>(`/practice/drill-in/resume?topic=${encodeURIComponent(topic)}`),

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
  startSession: (subject: string, mode: string, topic?: string | null, skill?: string | null) =>
    apiFetch<StartSessionResponse>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({
        subject,
        session_type: mode,
        ...(topic ? { topic } : {}),
        ...(skill ? { return_to: `marker_skill:${skill}` } : {}),
      }),
    }),
};
