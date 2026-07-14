"use client";

import { useEffect } from "react";
import { SegmentBand, type SegmentDisplay } from "./segment-band";
import { ExitSessionButton } from "./exit-session-button";
import { AlexDrawer } from "./alex-drawer";

interface SessionShellProps {
  segments: SegmentDisplay[];
  children: React.ReactNode;
  /** Session ID passed through to AlexDrawer for context-aware chat. */
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
export function SessionShell({ segments, children, sessionId }: SessionShellProps) {
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

      {/* Main content area — Task 10 fills this in */}
      <main className="flex-1">{children}</main>

      {/* Bottom action bar slot — Task 13 */}

      {/* Alex drawer — always mounted so history + draft persist */}
      {sessionId && <AlexDrawer sessionId={sessionId} />}
    </div>
  );
}
