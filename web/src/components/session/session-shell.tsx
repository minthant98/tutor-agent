"use client";

import { useEffect } from "react";
import { SegmentBand, type SegmentDisplay } from "./segment-band";
import { ExitSessionButton } from "./exit-session-button";

interface SessionShellProps {
  segments: SegmentDisplay[];
  children: React.ReactNode;
  /** Session ID — kept for API compatibility; the drawer is mounted globally by AppShell. */
  sessionId?: string;
}

/**
 * SessionShell — full-viewport focus mode for active sessions.
 *
 * Mounts a `data-session-focus="true"` attribute on `<html>` so that global
 * CSS in globals.css hides the AppShell sidebar and top-bar while a session
 * is in progress. The attribute is cleaned up on unmount.
 *
 * Layout:
 *   ┌─────────────────────────────────┐
 *   │  SegmentBand (sticky, 56px)     │
 *   │                    [Exit btn]   │
 *   ├─────────────────────────────────┤
 *   │  main content (flex-1, Task 10) │
 *   └─────────────────────────────────┘
 *
 * The bottom action bar slot is left open for Task 13.
 */
export function SessionShell({ segments, children }: SessionShellProps) {
  // Set / clear the focus-mode attribute on <html>
  useEffect(() => {
    document.documentElement.setAttribute("data-session-focus", "true");
    return () => {
      document.documentElement.removeAttribute("data-session-focus");
    };
  }, []);

  return (
    <div className="relative min-h-screen bg-[var(--surface-0)] flex flex-col">
      {/* Progress band */}
      <SegmentBand segments={segments} />

      {/* Exit button — absolute top-right */}
      <ExitSessionButton className="absolute top-2 right-2" />

      {/* Main content area */}
      <main className="flex-1">{children}</main>

      {/* Alex drawer is mounted globally by AppShell (reads sessionId from pathname) */}
    </div>
  );
}
