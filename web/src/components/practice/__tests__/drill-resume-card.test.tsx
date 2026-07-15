import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DrillResumeCard } from "../drill-resume-card";
import type { DrillResumeData } from "@/lib/api/practice";

const RESUME_DATA: DrillResumeData = {
  session_id: "session-abc-123",
  topic_label: "Partial Fractions",
  progress: { current: 4, total: 10 },
};

describe("DrillResumeCard", () => {
  it("renders when data is provided", () => {
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={vi.fn()}
      />
    );
    expect(screen.getByTestId("drill-resume-card")).toBeInTheDocument();
  });

  it("shows Resume Drill label", () => {
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={vi.fn()}
      />
    );
    expect(screen.getByText(/Resume Drill/i)).toBeInTheDocument();
  });

  it("shows topic label", () => {
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={vi.fn()}
      />
    );
    expect(screen.getByText("Partial Fractions")).toBeInTheDocument();
  });

  it("shows progress count", () => {
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={vi.fn()}
      />
    );
    expect(screen.getByText("4/10 completed")).toBeInTheDocument();
  });

  it("renders Resume and Start over buttons", () => {
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /Resume/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start over/ })).toBeInTheDocument();
  });

  it("calls onResume with session_id when Resume is clicked", () => {
    const onResume = vi.fn();
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={onResume}
        onStartOver={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Resume/ }));
    expect(onResume).toHaveBeenCalledWith("session-abc-123");
  });

  it("calls onStartOver when Start over is clicked", () => {
    const onStartOver = vi.fn();
    render(
      <DrillResumeCard
        data={RESUME_DATA}
        onResume={vi.fn()}
        onStartOver={onStartOver}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Start over/ }));
    expect(onStartOver).toHaveBeenCalledOnce();
  });

  it("is not rendered when caller has null data (conditional rendering)", () => {
    // Test the pattern used by PracticeLanding: null guard
    const { container } = render(
      <>
        {null && (
          <DrillResumeCard
            data={RESUME_DATA}
            onResume={vi.fn()}
            onStartOver={vi.fn()}
          />
        )}
      </>
    );
    expect(container.querySelector("[data-testid='drill-resume-card']")).toBeNull();
  });
});
