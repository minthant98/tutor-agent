import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { SegmentTransition } from "../segment-transition";

describe("SegmentTransition", () => {
  it("shows 'Segment Complete' header and prev intent", () => {
    render(
      <SegmentTransition
        prev={{ intent: "reinforce" }}
        next={{ intent: "assess", topic: "Differentiation", minutes: 6 }}
        onContinue={vi.fn()}
      />
    );
    expect(screen.getByText(/Segment Complete/)).toBeInTheDocument();
    expect(screen.getByText(/Reinforce finished\./)).toBeInTheDocument();
  });

  it("shows 'Next' header and next intent · topic", () => {
    render(
      <SegmentTransition
        prev={{ intent: "reinforce" }}
        next={{ intent: "assess", topic: "Differentiation", minutes: 6 }}
        onContinue={vi.fn()}
      />
    );
    expect(screen.getByText(/Assess · Differentiation/)).toBeInTheDocument();
  });

  it("shows minutes remaining for next segment", () => {
    render(
      <SegmentTransition
        prev={{ intent: "reinforce" }}
        next={{ intent: "assess", topic: "Differentiation", minutes: 6 }}
        onContinue={vi.fn()}
      />
    );
    expect(screen.getByText(/≈ 6 minutes/)).toBeInTheDocument();
  });

  it("↵ calls onContinue", async () => {
    const user = userEvent.setup();
    const onContinue = vi.fn();
    render(
      <SegmentTransition
        prev={{ intent: "teach" }}
        next={{ intent: "assess", topic: "X", minutes: 5 }}
        onContinue={onContinue}
      />
    );
    await user.keyboard("{Enter}");
    expect(onContinue).toHaveBeenCalled();
  });

  it("renders the Continue button", () => {
    render(
      <SegmentTransition
        prev={{ intent: "teach" }}
        next={{ intent: "reinforce", topic: "Integration", minutes: 8 }}
        onContinue={vi.fn()}
      />
    );
    expect(
      screen.getByRole("button", { name: /Continue/i })
    ).toBeInTheDocument();
  });

  it("has role=dialog and aria-modal=true for accessibility", () => {
    render(
      <SegmentTransition
        prev={{ intent: "teach" }}
        next={{ intent: "assess", topic: "Limits", minutes: 4 }}
        onContinue={vi.fn()}
      />
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });
});
