"use client";

import { useState } from "react";
import { Switch } from "@/components/ui/switch";

interface NotifRow {
  id: string;
  label: string;
  description: string;
}

const NOTIF_ROWS: NotifRow[] = [
  {
    id: "session_reminders",
    label: "Session reminders",
    description: "Daily nudge to keep your study streak alive.",
  },
  {
    id: "weekly_digest",
    label: "Weekly digest",
    description: "A summary of your progress and upcoming topics.",
  },
  {
    id: "marker_results",
    label: "Marker results",
    description: "Email when your graded submission is ready.",
  },
];

type NotifState = Record<string, boolean>;

export function NotificationsSection() {
  // TODO: wire backend — load from student.preferences or a dedicated prefs endpoint
  const [prefs, setPrefs] = useState<NotifState>({
    session_reminders: true,
    weekly_digest: true,
    marker_results: true,
  });

  function toggle(id: string) {
    setPrefs((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      // TODO: PATCH /account/preferences with notification prefs when backend lands
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">
        Notifications
      </h2>

      <div className="space-y-0 divide-y divide-[var(--border-subtle)]">
        {NOTIF_ROWS.map(({ id, label, description }) => (
          <div key={id} className="flex items-center justify-between py-4">
            <div>
              <p className="text-[14px] font-medium text-[var(--text-primary)]">
                {label}
              </p>
              <p className="text-[12px] text-[var(--text-secondary)] mt-0.5">
                {description}
              </p>
            </div>
            <Switch
              id={`notif-${id}`}
              checked={prefs[id] ?? false}
              onCheckedChange={() => toggle(id)}
              aria-label={label}
            />
          </div>
        ))}
      </div>

      <p className="text-[12px] text-[var(--text-muted)]">
        TODO: wire backend — notification preferences are currently on-page only
        and reset on refresh.
      </p>
    </div>
  );
}
