import { apiFetch } from "@/lib/api";

export interface ChartPoint {
  date: string;
  readiness: number;
}

export interface MasteryTopicItem {
  id: string;
  label: string;
  mastery: number;
}

export interface SessionHistoryItem {
  id: string;
  date: string;
  mode: string;
  topic?: string | null;
  duration_minutes: number;
  delta_readiness: number;
}

export interface MarkerHistoryItem {
  id: string;
  date: string;
  marks?: number | null;
  max_marks: number;
  delta_readiness: number;
}

export interface WeeklyStatsData {
  sessions_this_week: number;
  questions_attempted: number;
  marks_scored: number;
  marks_max: number;
  time_in_app_minutes: number;
}

export interface ProgressV3 {
  narration: string;
  chart_series: ChartPoint[];
  readiness_current: number;
  readiness_delta_14d: number;
  mastery_by_topic: MasteryTopicItem[];
  session_history: SessionHistoryItem[];
  marker_history_compact: MarkerHistoryItem[];
  weekly_stats: WeeklyStatsData;
}

export const progressApi = {
  getV3: (subject: string, days: 30 | 90 = 30): Promise<ProgressV3> =>
    apiFetch<ProgressV3>(
      `/progress/v3?subject=${encodeURIComponent(subject)}&days=${days}`
    ),
};
