import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ProcessingStates } from "../processing-states";

describe("ProcessingStates", () => {
  it.each([
    ["uploading", /Uploading your photos/],
    ["extracting", /Reading your handwriting/],
    ["grading", /Alex is marking your answer/],
  ] as const)("shows %s copy", (status, expected) => {
    render(<ProcessingStates status={status as any} />);
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it("does not show any percentage", () => {
    render(<ProcessingStates status="grading" />);
    const text = document.body.textContent!;
    expect(text).not.toMatch(/\d+%/);
  });

  it("returns null when status is graded", () => {
    const { container } = render(<ProcessingStates status="graded" />);
    expect(container.firstChild).toBeNull();
  });

  describe("error state", () => {
    it("renders matter-of-fact copy for extraction error", () => {
      render(<ProcessingStates status="error" kind="extraction" onRetry={vi.fn()} />);
      expect(
        screen.getByText(
          /Couldn't read that photo clearly — please retake or try typing your answer\./
        )
      ).toBeInTheDocument();
    });

    it("renders matter-of-fact copy for grading error", () => {
      render(<ProcessingStates status="error" kind="grading" onRetry={vi.fn()} />);
      expect(
        screen.getByText(/Marking hasn't finished — try again in a moment\./)
      ).toBeInTheDocument();
    });

    it("renders a retry button for extraction error", () => {
      render(<ProcessingStates status="error" kind="extraction" onRetry={vi.fn()} />);
      expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
    });

    it("renders a retry button for grading error", () => {
      render(<ProcessingStates status="error" kind="grading" onRetry={vi.fn()} />);
      expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
    });

    it("calls onRetry when retry button is clicked", async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();
      render(<ProcessingStates status="error" kind="extraction" onRetry={onRetry} />);
      await user.click(screen.getByRole("button", { name: /try again/i }));
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it("does not render retry button when onRetry is not provided", () => {
      render(<ProcessingStates status="error" kind="extraction" />);
      expect(screen.queryByRole("button", { name: /try again/i })).not.toBeInTheDocument();
    });

    it("does not show any percentage in error state", () => {
      render(<ProcessingStates status="error" kind="grading" onRetry={vi.fn()} />);
      const text = document.body.textContent!;
      expect(text).not.toMatch(/\d+%/);
    });
  });
});
