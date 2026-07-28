import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { SessionShell } from "../session-shell";

// --- Mock sub-components to keep tests focused on SessionShell behaviour ---
vi.mock("../segment-band", () => ({
  SegmentBand: ({ segments }: { segments: unknown[] }) => (
    <div data-testid="segment-band" data-count={segments.length} />
  ),
}));

// Mock ExitSessionButton to a simplified version that exposes the dialog
vi.mock("../exit-session-button", () => ({
  ExitSessionButton: ({ className }: { className?: string }) => {
    const { useState } = require("react");
    const [open, setOpen] = useState(false);
    return (
      <>
        <button
          data-testid="exit-btn"
          className={className}
          onClick={() => setOpen(true)}
          aria-label="Exit session"
        />
        {open && (
          <div role="dialog" aria-label="Exit this session?">
            <p>Your progress is saved. You can resume from the dashboard.</p>
            <button
              data-testid="cancel-btn"
              onClick={() => setOpen(false)}
            >
              Cancel
            </button>
            <button data-testid="confirm-exit-btn">Exit</button>
          </div>
        )}
      </>
    );
  },
}));

// Mock Next.js router
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

const SEGMENTS = [
  { intent: "teach", topic: "Integration", state: "completed" as const },
  {
    intent: "reinforce",
    topic: "Substitution",
    state: "current" as const,
    minutesRemaining: 7,
  },
  { intent: "assess", topic: "Partial Fractions", state: "upcoming" as const },
];

function renderShell() {
  return render(
    <SessionShell segments={SEGMENTS}>
      <div data-testid="session-content">Content</div>
    </SessionShell>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("SessionShell", () => {
  beforeEach(() => {
    // Reset any leftover attribute between tests
    document.documentElement.removeAttribute("data-session-focus");
  });

  it("sets data-session-focus='true' on <html> when mounted", () => {
    renderShell();
    expect(document.documentElement).toHaveAttribute(
      "data-session-focus",
      "true"
    );
  });

  it("removes data-session-focus from <html> when unmounted", () => {
    const { unmount } = renderShell();
    expect(document.documentElement).toHaveAttribute("data-session-focus");
    unmount();
    expect(document.documentElement).not.toHaveAttribute("data-session-focus");
  });

  it("renders children in the main content slot", () => {
    renderShell();
    expect(screen.getByTestId("session-content")).toBeInTheDocument();
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("renders SegmentBand with the correct segment count", () => {
    renderShell();
    const band = screen.getByTestId("segment-band");
    expect(band).toBeInTheDocument();
    expect(band).toHaveAttribute("data-count", "3");
  });

  it("renders the exit button in the top-right corner", () => {
    renderShell();
    expect(screen.getByTestId("exit-btn")).toBeInTheDocument();
  });

  it("exit button opens confirm dialog on click", async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByTestId("exit-btn"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("cancel closes dialog without navigating", async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByTestId("exit-btn"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getByTestId("cancel-btn"));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
