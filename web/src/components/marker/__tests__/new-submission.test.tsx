import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { NewSubmission } from "../new-submission";

// analytics.ts capture — no-op in tests (no window.posthog)
vi.mock("@/lib/analytics", () => ({ capture: vi.fn() }));

const SAMPLE_QUESTION = {
  id: "q_test_001",
  text: "Find the derivative of f(x) = x³ − 3x + 2.",
  max_marks: 4,
  paper_ref: "Edexcel 9MA0 · 2024 Q5",
  mark_scheme: "M1: differentiate term by term\nA1: 3x² − 3\nA1: correct notation\nA1: simplified",
};

describe("NewSubmission", () => {
  it("renders question text", () => {
    render(<NewSubmission question={SAMPLE_QUESTION} />);
    expect(
      screen.getByText(/Find the derivative of f\(x\) = x³/)
    ).toBeInTheDocument();
  });

  it("renders marks chip with correct count", () => {
    render(<NewSubmission question={SAMPLE_QUESTION} />);
    expect(screen.getByText(/4 marks/)).toBeInTheDocument();
  });

  it("renders paper_ref", () => {
    render(<NewSubmission question={SAMPLE_QUESTION} />);
    expect(screen.getByText(/Edexcel 9MA0 · 2024 Q5/)).toBeInTheDocument();
  });

  it("renders MarkSchemePeek in default (hidden) state", () => {
    render(<NewSubmission question={SAMPLE_QUESTION} />);
    // The peek component shows "Available after submission" in hidden state
    expect(screen.getByText(/Available after submission/)).toBeInTheDocument();
    // Scheme text should NOT be visible
    expect(screen.queryByText(/M1: differentiate/)).not.toBeInTheDocument();
  });

  it("shows answer placeholder area", () => {
    render(<NewSubmission question={SAMPLE_QUESTION} />);
    expect(screen.getByRole("region", { name: /your answer/i })).toBeInTheDocument();
  });
});
