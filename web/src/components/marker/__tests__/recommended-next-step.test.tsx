import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock analytics so no window.posthog needed in jsdom
vi.mock("@/lib/analytics", () => ({ capture: vi.fn() }));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

import { RecommendedNextStep } from "../recommended-next-step";
import { capture } from "@/lib/analytics";

const SAMPLE_RECOMMENDATION = {
  topic_id: "integration_basics",
  sub_skill: "substitution",
  blurb: "Practice substitution with one targeted question.",
};

describe("RecommendedNextStep", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the blurb text", () => {
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );
    expect(
      screen.getByText("Practice substitution with one targeted question.")
    ).toBeInTheDocument();
  });

  it("renders section header 'Recommended next step'", () => {
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );
    expect(screen.getByText("Recommended next step")).toBeInTheDocument();
  });

  it("renders Start Practice button", () => {
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );
    expect(
      screen.getByRole("button", { name: /Start Practice/i })
    ).toBeInTheDocument();
  });

  it("clicking Start Practice fires capture with correct props", async () => {
    const user = userEvent.setup();
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );

    await user.click(screen.getByRole("button", { name: /Start Practice/i }));

    expect(capture).toHaveBeenCalledWith(
      "marker_recommended_practice_clicked",
      {
        submission_id: "sub-001",
        topic_id: "integration_basics",
        sub_skill: "substitution",
      }
    );
  });

  it("clicking Start Practice calls router.push with correct URL including submission_id", async () => {
    const user = userEvent.setup();
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );

    await user.click(screen.getByRole("button", { name: /Start Practice/i }));

    expect(mockPush).toHaveBeenCalledWith(
      "/practice/plan?mode=drill_in&topic=integration_basics&skill=substitution&submission_id=sub-001"
    );
  });

  it("fires capture before navigating (capture called exactly once)", async () => {
    const user = userEvent.setup();
    render(
      <RecommendedNextStep
        submissionId="sub-001"
        recommendation={SAMPLE_RECOMMENDATION}
      />
    );

    await user.click(screen.getByRole("button", { name: /Start Practice/i }));

    expect(capture).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledTimes(1);
  });
});
