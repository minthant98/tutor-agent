/**
 * Static command items for the Cmd-K palette.
 *
 * ACTIONS — always shown (first section, not filtered by backend search)
 * ACCOUNT_ITEMS — always shown (last section)
 * NAV_ITEMS — static navigation links shown in the Navigate section
 */

export interface CmdItem {
  id: string;
  label: string;
  href: string;
  shortcut?: string;
  subtitle?: string;
}

export const ACTIONS: CmdItem[] = [
  {
    id: "action:start-session",
    label: "Start Today's Session",
    href: "/sessions/new",
    shortcut: "⌘S",
  },
  {
    id: "action:exam-marker",
    label: "Open Exam Marker",
    href: "/mark",
    shortcut: "⌘M",
  },
  {
    id: "action:ask-alex",
    label: "Ask Alex",
    href: "/alex",
    shortcut: "⌘A",
  },
  {
    id: "action:practice",
    label: "Start Practice",
    href: "/practice",
  },
];

export const ACCOUNT_ITEMS: CmdItem[] = [
  {
    id: "account:toggle-theme",
    label: "Toggle theme",
    href: "#toggle-theme",
  },
  {
    id: "account:settings",
    label: "Settings",
    href: "/settings",
  },
  {
    id: "account:sign-out",
    label: "Sign out",
    href: "/auth/logout",
  },
];

export const NAV_ITEMS: CmdItem[] = [
  {
    id: "nav:dashboard",
    label: "Dashboard",
    href: "/dashboard",
  },
  {
    id: "nav:topics",
    label: "Topics",
    href: "/topics",
  },
  {
    id: "nav:sessions",
    label: "Sessions",
    href: "/sessions",
  },
  {
    id: "nav:practice",
    label: "Practice",
    href: "/practice",
  },
];
