import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { TopicCard } from "../topic-card";
import type { TopicV3 } from "../types";

// Mock next/navigation and next/link for test environment
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

const BASE_TOPIC: TopicV3 = {
  id: "integration_basics",
  label: "Integration Basics",
  mastery: 64,
  last_practised: "2 days ago",
  status: "Needs review",
  prerequisite: null,
};

describe("TopicCard", () => {
  it("shows only the four required fields", () => {
    render(<TopicCard topic={BASE_TOPIC} />);
    expect(screen.getByText("Integration Basics")).toBeInTheDocument();
    expect(screen.getByText("64%")).toBeInTheDocument();
    expect(screen.getByText("2 days ago")).toBeInTheDocument();
    expect(screen.getByText("Needs review")).toBeInTheDocument();
    // NOT expected: progress bar (spec says no progress bar)
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("shows a prerequisite link when provided", () => {
    render(
      <TopicCard
        topic={{
          ...BASE_TOPIC,
          prerequisite: { id: "chain_rule", label: "Chain rule", affects_this: true },
        }}
      />
    );
    expect(screen.getByText(/Chain rule fluency affects this topic/)).toBeInTheDocument();
  });

  it("uses Alex note when mastery of prerequisite is low", () => {
    render(
      <TopicCard
        topic={{
          ...BASE_TOPIC,
          prerequisite: {
            id: "chain_rule",
            label: "Chain rule",
            affects_this: true,
            alex_note: "Weak chain rule is dragging this down.",
          },
        }}
      />
    );
    expect(screen.getByText(/Weak chain rule is dragging this down\./)).toBeInTheDocument();
  });

  it("does not show prerequisite section when prerequisite is null", () => {
    render(<TopicCard topic={BASE_TOPIC} />);
    expect(screen.queryByText(/fluency affects/)).not.toBeInTheDocument();
  });

  it("renders card as a navigable element with link role", () => {
    render(<TopicCard topic={BASE_TOPIC} />);
    // The card uses role="link" on a div (to avoid nested-<a> hydration issue
    // when a prerequisite link is present).
    const card = screen.getByRole("link", { name: /Integration Basics/ });
    expect(card).toBeInTheDocument();
    expect(card).toHaveAttribute("data-href", "/topics/integration_basics");
  });

  it("shows 'Never' for last practised when not started", () => {
    render(
      <TopicCard
        topic={{ ...BASE_TOPIC, mastery: 0, status: "Not started", last_practised: "Never" }}
      />
    );
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("shows Mastered status badge", () => {
    render(
      <TopicCard
        topic={{ ...BASE_TOPIC, mastery: 85, status: "Mastered", last_practised: "today" }}
      />
    );
    expect(screen.getByText("Mastered")).toBeInTheDocument();
  });

  it("does not render PrerequisiteLink when affects_this is false", () => {
    render(
      <TopicCard
        topic={{
          ...BASE_TOPIC,
          prerequisite: { id: "chain_rule", label: "Chain rule", affects_this: false },
        }}
      />
    );
    expect(screen.queryByText(/Chain rule fluency affects this topic/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /chain rule/i })).not.toBeInTheDocument();
  });
});
