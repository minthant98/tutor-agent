import { apiFetch } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";

export const dashboardApi = {
  get: (subject: string): Promise<DashboardPayload> =>
    apiFetch<DashboardPayload>(`/dashboard/${subject}`),
};
