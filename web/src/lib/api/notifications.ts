import { apiFetch } from "@/lib/api";
import type { NotificationListOut } from "@/lib/types";

export const notificationsApi = {
  list: (): Promise<NotificationListOut> =>
    apiFetch<NotificationListOut>("/notifications"),

  markRead: (ids: string[]): Promise<void> =>
    apiFetch<void>("/notifications/mark-read", {
      method: "POST",
      body: JSON.stringify({ ids }),
    }),

  markAllRead: (): Promise<void> =>
    apiFetch<void>("/notifications/mark-all-read", { method: "POST" }),
};
