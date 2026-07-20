import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { MarkerLanding } from "../marker-landing";
import type { MarkerV3LandingData } from "@/lib/types";

// Mock next/navigation (used by child components)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const SAMPLE_QUESTION = {
  id: "q_abc",
  text: "Integrate x^2 from 0 to 1",
  max_marks: 4,
  paper_ref: "Edexcel 9MA0 · 2024 Q3",
};

const SAMPLE: MarkerV3LandingData = {
  narration:
    "Integration accuracy averaged 62% across the last four submissions. Today's question targets substitution.",
  question: SAMPLE_QUESTION,
  refresh_count_used: 0,
  refresh_limit: 5,
  tier: "free",
  recent_submissions: [],
};

describe("MarkerLanding", () => {
  it("shows refresh counter for free tier", () => {
    render(
      <MarkerLanding
        data={{ ...SAMPLE, refresh_count_used: 3, refresh_limit: 5, tier: "free" }}
        onRefresh={vi.fn()}
      />
    );
    // 5 - 3 = 2 remaining
    expect(screen.getByText(/2 free refreshes remaining/)).toBeInTheDocument();
  });

  it("hides refresh counter for pro", () => {
    render(
      <MarkerLanding
        data={{ ...SAMPLE, refresh_count_used: 3, refresh_limit: null, tier: "pro" }}
        onRefresh={vi.fn()}
      />
    );
    expect(screen.queryByText(/free refreshes remaining/)).not.toBeInTheDocument();
  });

  it("shows narration in analytical framing", () => {
    render(
      <MarkerLanding
        data={{
          ...SAMPLE,
          narration:
            "Integration accuracy averaged 62% across the last four submissions. Today's question targets substitution.",
        }}
        onRefresh={vi.fn()}
      />
    );
    expect(
      screen.getByText(/Integration accuracy averaged 62%/)
    ).toBeInTheDocument();
  });

  it("renders the question text", () => {
    render(<MarkerLanding data={SAMPLE} onRefresh={vi.fn()} />);
    expect(screen.getByText(/Integrate x\^2 from 0 to 1/)).toBeInTheDocument();
  });

  it("renders the marks chip with correct count", () => {
    render(<MarkerLanding data={SAMPLE} onRefresh={vi.fn()} />);
    expect(screen.getByText(/4 marks/)).toBeInTheDocument();
  });

  it("renders the paper ref", () => {
    render(<MarkerLanding data={SAMPLE} onRefresh={vi.fn()} />);
    expect(screen.getByText(/Edexcel 9MA0 · 2024 Q3/)).toBeInTheDocument();
  });

  it("renders submit CTA", () => {
    render(<MarkerLanding data={SAMPLE} onRefresh={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /submit an answer to this question/i })
    ).toBeInTheDocument();
  });

  it("calls onRefresh when ghost button clicked", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();
    render(
      <MarkerLanding
        data={{ ...SAMPLE, refresh_count_used: 1, refresh_limit: 5, tier: "free" }}
        onRefresh={onRefresh}
      />
    );
    const refreshBtn = screen.getByRole("button", { name: /different question/i });
    await user.click(refreshBtn);
    expect(onRefresh).toHaveBeenCalledOnce();
  });

  it("shows empty state when no recent submissions", () => {
    render(
      <MarkerLanding data={{ ...SAMPLE, recent_submissions: [] }} onRefresh={vi.fn()} />
    );
    expect(screen.getByText(/no submissions yet/i)).toBeInTheDocument();
  });

  it("renders recent submissions rows", () => {
    const submissions = [
      {
        id: "sub-1",
        created_at: "2026-07-18T10:00:00Z",
        marks: 3,
        max_marks: 4,
        delta_readiness: 2,
        question_preview: "Integrate x^2 from 0 to 1",
      },
    ];
    render(
      <MarkerLanding
        data={{ ...SAMPLE, recent_submissions: submissions }}
        onRefresh={vi.fn()}
      />
    );
    expect(screen.getByText(/3\/4/)).toBeInTheDocument();
    expect(screen.getByText(/\+2/)).toBeInTheDocument();
  });

  it("shows 1 free refresh remaining correctly (singular)", () => {
    render(
      <MarkerLanding
        data={{ ...SAMPLE, refresh_count_used: 4, refresh_limit: 5, tier: "free" }}
        onRefresh={vi.fn()}
      />
    );
    expect(screen.getByText(/1 free refresh remaining/)).toBeInTheDocument();
  });
});
