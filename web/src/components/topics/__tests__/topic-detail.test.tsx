import { render, screen, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TopicDetail } from "../topic-detail";
import type { TopicDetailV3 } from "../types";

// Mock next/link for test environment
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// ── Fixtures ──────────────────────────────────────────────────────────────────

const SAMPLE: TopicDetailV3 = {
  topic: {
    id: "integration_basics",
    label: "Integration Basics",
    mastery: 64,
    syllabus_ref: "Edexcel · Topic 14",
    target_grade: "A",
  },
  common_mistakes: [
    {
      text: "Across your last three attempts, substitution was correct, but limits of integration caused the lost marks.",
      evidence_submission_ids: ["uuid-1", "uuid-2"],
    },
  ],
  recent_attempts: [
    {
      id: "attempt-1",
      created_at: "2026-07-10T10:00:00Z",
      marks: 4,
      max_marks: 6,
      question_preview: "Integrate x^2 from 0 to 1",
    },
  ],
  recommended_practice_href: "/practice/plan?mode=drill_in&topic=integration_basics",
  related_topics: [
    {
      id: "differentiation_basics",
      label: "Differentiation Basics",
      relation: "prerequisite",
    },
  ],
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("TopicDetail", () => {
  it("renders exactly the five sections in fixed order", () => {
    render(<TopicDetail data={SAMPLE} />);
    const sections = screen
      .getAllByRole("region")
      .map((s) => s.getAttribute("aria-label"));
    expect(sections).toEqual([
      "Overview",
      "Common mistakes",
      "Recent attempts",
      "Recommended practice",
      "Related topics",
    ]);
  });

  it("Overview shows topic name, mastery, syllabus_ref, and target grade", () => {
    render(<TopicDetail data={SAMPLE} />);
    const overview = screen.getByRole("region", { name: "Overview" });
    expect(within(overview).getByText("Integration Basics")).toBeInTheDocument();
    expect(within(overview).getByText("64%")).toBeInTheDocument();
    expect(within(overview).getByText("Edexcel · Topic 14")).toBeInTheDocument();
    expect(within(overview).getByText(/Target grade/)).toBeInTheDocument();
    expect(within(overview).getByText("A")).toBeInTheDocument();
  });

  it("Common mistakes shows analytical evidence-backed text, no generic tips", () => {
    render(
      <TopicDetail
        data={{
          ...SAMPLE,
          common_mistakes: [
            {
              text: "Across your last three attempts, substitution was correct, but limits of integration caused the lost marks.",
              evidence_submission_ids: ["uuid-1", "uuid-2"],
            },
          ],
        }}
      />
    );
    const region = screen.getByRole("region", { name: "Common mistakes" });
    expect(
      within(region).getByText(/Across your last three attempts/)
    ).toBeInTheDocument();
  });

  it("omits Common mistakes when no evidence exists (fresh student)", () => {
    render(<TopicDetail data={{ ...SAMPLE, common_mistakes: [] }} />);
    expect(
      screen.queryByRole("region", { name: "Common mistakes" })
    ).not.toBeInTheDocument();
  });

  it("Common mistakes shows evidence chip with attempt count", () => {
    render(<TopicDetail data={SAMPLE} />);
    const region = screen.getByRole("region", { name: "Common mistakes" });
    expect(within(region).getByText(/Evidence: 2 attempts/)).toBeInTheDocument();
  });

  it("shows 5 sections in order even when Common mistakes is hidden (fresh student)", () => {
    render(
      <TopicDetail
        data={{
          ...SAMPLE,
          common_mistakes: [],
          related_topics: [
            { id: "diff", label: "Differentiation", relation: "prerequisite" },
          ],
        }}
      />
    );
    const sections = screen
      .getAllByRole("region")
      .map((s) => s.getAttribute("aria-label"));
    // Common mistakes is hidden; only 4 sections visible
    expect(sections).toEqual([
      "Overview",
      "Recent attempts",
      "Recommended practice",
      "Related topics",
    ]);
  });

  it("Recent attempts lists attempts with date, marks, and preview", () => {
    render(<TopicDetail data={SAMPLE} />);
    const region = screen.getByRole("region", { name: "Recent attempts" });
    expect(within(region).getByText("4/6")).toBeInTheDocument();
    expect(within(region).getByText(/Integrate x\^2/)).toBeInTheDocument();
  });

  it("Recent attempts links each attempt to /mark/{id}", () => {
    render(<TopicDetail data={SAMPLE} />);
    const link = screen.getByRole("link", { name: /Integrate x\^2/ });
    expect(link).toHaveAttribute("href", "/mark/attempt-1");
  });

  it("Recent attempts shows 'No attempts yet' message for fresh student", () => {
    render(<TopicDetail data={{ ...SAMPLE, recent_attempts: [] }} />);
    const region = screen.getByRole("region", { name: "Recent attempts" });
    expect(within(region).getByText(/No attempts yet/)).toBeInTheDocument();
  });

  it("Recommended practice has primary CTA linking to recommended_practice_href", () => {
    render(<TopicDetail data={SAMPLE} />);
    const region = screen.getByRole("region", { name: "Recommended practice" });
    const cta = within(region).getByRole("link", { name: /Practice this topic/ });
    expect(cta).toHaveAttribute(
      "href",
      "/practice/plan?mode=drill_in&topic=integration_basics"
    );
  });

  it("Related topics shows related topic link cards", () => {
    render(<TopicDetail data={SAMPLE} />);
    const region = screen.getByRole("region", { name: "Related topics" });
    expect(
      within(region).getByText(/Differentiation Basics/)
    ).toBeInTheDocument();
  });

  it("omits Related topics when empty list", () => {
    render(<TopicDetail data={{ ...SAMPLE, related_topics: [] }} />);
    expect(
      screen.queryByRole("region", { name: "Related topics" })
    ).not.toBeInTheDocument();
  });

  it("Related topics links to /topics/{id}", () => {
    render(<TopicDetail data={SAMPLE} />);
    const link = screen.getByRole("link", { name: /Differentiation Basics/ });
    expect(link).toHaveAttribute("href", "/topics/differentiation_basics");
  });
});
