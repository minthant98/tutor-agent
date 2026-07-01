"use client";
import { useEffect, useState } from "react";
import { notificationsApi } from "@/lib/api/notifications";
import { useFeatureFlag } from "@/lib/feature-flags";
import type { NotificationOut } from "@/lib/types";

export function NotificationBell() {
  const enabled = useFeatureFlag("notifications_v2", true);
  const [unread, setUnread] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!enabled) return;
    notificationsApi
      .list()
      .then((r) => {
        setUnread(r.unread_count);
        setItems(r.items.slice(0, 20));
        setError(false);
      })
      .catch(() => {
        setUnread(null);
        setError(true);
      });
  }, [enabled, open]);

  if (!enabled) return null;

  return (
    <div className="relative">
      <button onClick={() => setOpen((v) => !v)} className="relative p-2">
        <BellIcon />
        {unread != null && unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-md border border-[var(--border)] bg-white shadow-lg">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <h3 className="font-semibold">Notifications</h3>
            <button
              className="text-xs text-[var(--blue)]"
              onClick={async () => {
                await notificationsApi.markAllRead();
                setUnread(0);
              }}
            >
              Mark all read
            </button>
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {error ? (
              <li className="px-3 py-6 text-center text-sm text-[var(--text-secondary)]">
                Could not load notifications.
              </li>
            ) : items.length === 0 ? (
              <li className="px-3 py-6 text-center text-sm text-[var(--text-secondary)]">
                No notifications yet.
              </li>
            ) : (
              items.map((n) => (
                <li
                  key={n.id}
                  className={`border-b px-3 py-2 text-sm ${!n.read_at ? "bg-blue-50" : ""}`}
                >
                  {labelFor(n)}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

function labelFor(n: NotificationOut): string {
  switch (n.type) {
    case "readiness_increased":
      return `Your readiness increased by ${String(n.payload.delta)}%`;
    case "diagnostic_complete":
      return "Your diagnostic is ready — view your roadmap";
    case "subscription_renewed":
      return "Your Pro subscription renewed";
    case "session_reminder":
      return typeof n.payload.message === "string"
        ? n.payload.message
        : "Time for today's session";
    default:
      return n.type;
  }
}

function BellIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
      />
    </svg>
  );
}
