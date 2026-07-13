import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SegmentBand } from "../segment-band";

const SEGMENTS = [
  { intent: "teach", topic: "Integration", state: "completed" as const },
  {
    intent: "reinforce",
    topic: "Substitution",
    state: "current" as const,
    minutesRemaining: 7,
  },
  {
    intent: "assess",
    topic: "Partial Fractions",
    state: "upcoming" as const,
  },
];

describe("SegmentBand", () => {
  it("shows segment count label (Segment 2 of 3)", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    expect(screen.getByText(/Segment 2 of 3/)).toBeInTheDocument();
  });

  it("shows minutes remaining label (≈ 7 min remaining)", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    expect(screen.getByText(/≈ 7 min remaining/)).toBeInTheDocument();
  });

  it("labels current segment with Reinforce · Substitution", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    // Intent is uppercase in DOM, so match case-insensitively via regex
    expect(screen.getByText(/Reinforce/i)).toBeInTheDocument();
    expect(screen.getByText(/Substitution/)).toBeInTheDocument();
  });

  it("marks completed dot with aria-label containing 'completed'", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    const dots = screen.getAllByRole("listitem");
    expect(dots[0]).toHaveAttribute(
      "aria-label",
      expect.stringMatching(/completed/i)
    );
  });

  it("marks current dot with aria-current='step'", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    const dots = screen.getAllByRole("listitem");
    expect(dots[1]).toHaveAttribute("aria-current", "step");
  });

  it("marks upcoming dot with aria-label containing 'upcoming'", () => {
    render(<SegmentBand segments={SEGMENTS} />);
    const dots = screen.getAllByRole("listitem");
    expect(dots[2]).toHaveAttribute(
      "aria-label",
      expect.stringMatching(/upcoming/i)
    );
  });

  it("does not render minutes remaining when not provided", () => {
    const segs = SEGMENTS.map((s) =>
      s.state === "current" ? { ...s, minutesRemaining: undefined } : s
    );
    render(<SegmentBand segments={segs} />);
    expect(screen.queryByText(/min remaining/)).not.toBeInTheDocument();
  });
});
