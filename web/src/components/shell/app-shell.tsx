"use client";
import { useFeatureFlag } from "@/lib/feature-flags";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";
import { CmdK } from "./cmd-k";
import { ShortcutHelp } from "./shortcut-help";

/**
 * AppShell — top-level layout shell gated behind the `shell_v3` PostHog flag.
 *
 * When the flag is off (default), children are rendered unchanged — no layout
 * impact on existing pages.
 *
 * When the flag is on, wraps children in the full v3 layout:
 *   Sidebar | TopBar + main content area
 * Plus the floating CmdK palette and ShortcutHelp modal.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const v3Enabled = useFeatureFlag("shell_v3", true);

  if (!v3Enabled) return <>{children}</>;

  return (
    <div className="flex h-screen bg-[var(--surface-0)]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
      <CmdK />
      <ShortcutHelp />
    </div>
  );
}
