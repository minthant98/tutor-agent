import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DashboardHero } from "../dashboard-hero";

// Mock next/navigation since SessionCta uses useRouter
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const PAYLOAD = {
  narration:
    "Recent Integration accuracy dropped 12%. Today rebuilds the +C habit.",
  readiness_snapshot: {
    percent: 64,
    band: "A (borderline)",
    band_color_index: 1,
    target_grade: "A",
    days_to_exam: 42,
  },
  session_plan: [
    {
      intent: "reinforce",
      topic: "Integration Basics",
      why: "Rebuild +C habit",
      minutes: 8,
      questions: 3,
    },
    {
      intent: "assess",
      topic: "Partial Fractions",
      why: "Confirm current mastery",
      minutes: 7,
      questions: 2,
    },
    {
      intent: "teach",
      topic: "Definite Integrals",
      why: "New material",
      minutes: 7,
      questions: 1,
    },
  ],
  total_minutes: 22,
  resume_state: null,
};

describe("DashboardHero", () => {
  it("renders narration text", () => {
    render(<DashboardHero data={PAYLOAD} />);
    expect(
      screen.getByText(/Integration accuracy dropped/)
    ).toBeInTheDocument();
  });

  it("shows readiness percent and target grade", () => {
    render(<DashboardHero data={PAYLOAD} />);
    expect(screen.getByText("64%")).toBeInTheDocument();
    expect(screen.getByText(/Target: A/)).toBeInTheDocument();
  });

  it("shows total minutes and segment count", () => {
    render(<DashboardHero data={PAYLOAD} />);
    expect(screen.getByText(/22 minutes/)).toBeInTheDocument();
    expect(screen.getByText(/3 segments/)).toBeInTheDocument();
  });

  it("renders 'Start Today's Session' when no resume state", () => {
    render(<DashboardHero data={PAYLOAD} />);
    expect(
      screen.getByRole("button", { name: /start today's session/i })
    ).toBeInTheDocument();
  });

  it("renders 'Resume Today's Session' and segment info when mid-plan", () => {
    render(
      <DashboardHero
        data={{
          ...PAYLOAD,
          resume_state: { segment_index: 1, minutes_remaining: 14 },
        }}
      />
    );
    expect(
      screen.getByRole("button", { name: /resume today's session/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Segment 2 of 3/)).toBeInTheDocument();
  });
});
