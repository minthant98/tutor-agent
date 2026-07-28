import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ResultHero } from "../result-hero";

const defaultProps = {
  marks: 4,
  maxMarks: 6,
  gradePct: 67,
  readinessBefore: 64.2,
  readinessAfter: 66.4,
  targetGrade: "A",
};

describe("ResultHero", () => {
  it("renders marks in Geist Mono 40 — the largest visual element", () => {
    render(<ResultHero {...defaultProps} />);
    const marks = screen.getByTestId("result-marks");
    expect(marks).toBeInTheDocument();
    // Marks span must have the 40px mono class
    expect(marks.className).toContain("text-[40px]");
    expect(marks.className).toContain("font-mono");
    expect(marks.textContent).toBe("4 / 6");
  });

  it("renders grade % at 20px Geist Sans (secondary, smaller than marks)", () => {
    render(<ResultHero {...defaultProps} />);
    const gradePct = screen.getByTestId("result-grade-pct");
    expect(gradePct).toBeInTheDocument();
    expect(gradePct.className).toContain("text-[20px]");
    expect(gradePct.className).toContain("font-sans");
    expect(gradePct.textContent).toBe("67%");
  });

  it("grade % element does not have the 40px class (marks must be visually larger)", () => {
    render(<ResultHero {...defaultProps} />);
    const gradePct = screen.getByTestId("result-grade-pct");
    expect(gradePct.className).not.toContain("text-[40px]");
  });

  it("readiness displays rounded integers — not decimals", () => {
    render(<ResultHero {...defaultProps} />);
    // 64.2 → 64, 66.4 → 66
    expect(screen.getByText(/64 → 66/)).toBeInTheDocument();
  });

  it("does not display raw decimal readiness values", () => {
    render(<ResultHero {...defaultProps} />);
    const text = document.body.textContent ?? "";
    expect(text).not.toContain("64.2");
    expect(text).not.toContain("66.4");
  });

  it("shows the target grade", () => {
    render(<ResultHero {...defaultProps} />);
    expect(screen.getByText(/Target: A/)).toBeInTheDocument();
  });

  it("handles identical readiness before and after", () => {
    render(<ResultHero {...defaultProps} readinessBefore={65.0} readinessAfter={65.0} />);
    expect(screen.getByText(/65 → 65/)).toBeInTheDocument();
    expect(screen.getByText(/±0/)).toBeInTheDocument();
  });

  it("shows negative delta for a drop in readiness", () => {
    render(<ResultHero {...defaultProps} readinessBefore={68.0} readinessAfter={65.0} />);
    expect(screen.getByText(/68 → 65/)).toBeInTheDocument();
    expect(screen.getByText(/-3/)).toBeInTheDocument();
  });
});

describe("AlexFeedbackCard memory reference guard", () => {
  // Import here for co-location with the ResultHero test file
  // (brief specifies result-hero.test.tsx as the memory-ref test location)
  it("renders memory reference when memoryRef is provided", async () => {
    const { AlexFeedbackCard } = await import("../alex-feedback-card");
    render(
      <AlexFeedbackCard
        improvement="Practice chain rule — missed the outer derivative."
        memoryRef={{ text: "Your previous Integration attempt scored 40% — this one is higher.", evidence_days_ago: 5 }}
      />
    );
    expect(screen.getByTestId("alex-memory-ref")).toBeInTheDocument();
    expect(screen.getByText(/previous Integration attempt scored 40%/)).toBeInTheDocument();
  });

  it("does not render memory reference when memoryRef is null", async () => {
    const { AlexFeedbackCard } = await import("../alex-feedback-card");
    render(
      <AlexFeedbackCard
        improvement="Practice chain rule."
        memoryRef={null}
      />
    );
    expect(screen.queryByTestId("alex-memory-ref")).not.toBeInTheDocument();
  });

  it("does not render memory reference when memoryRef is undefined", async () => {
    const { AlexFeedbackCard } = await import("../alex-feedback-card");
    render(
      <AlexFeedbackCard
        improvement="Practice chain rule."
      />
    );
    expect(screen.queryByTestId("alex-memory-ref")).not.toBeInTheDocument();
  });
});
