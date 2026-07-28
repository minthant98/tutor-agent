import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// ── Mock next/link ────────────────────────────────────────────────────────────
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: { href: string; children: React.ReactNode; [key: string]: unknown }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// ── MasteryGrid ───────────────────────────────────────────────────────────────
import { MasteryGrid } from "../mastery-grid";

describe("MasteryGrid", () => {
  it("renders topic labels and mastery values", () => {
    render(
      <MasteryGrid
        topics={[
          { id: "integration", label: "Integration Basics", mastery: 64 },
          { id: "partial_fractions", label: "Partial Fractions", mastery: 30 },
        ]}
      />
    );
    expect(screen.getByText("Integration Basics")).toBeInTheDocument();
    expect(screen.getByText("64%")).toBeInTheDocument();
    expect(screen.getByText("Partial Fractions")).toBeInTheDocument();
    expect(screen.getByText("30%")).toBeInTheDocument();
  });

  it("shows empty state when topics list is empty", () => {
    render(<MasteryGrid topics={[]} />);
    expect(screen.getByText(/topics will appear/i)).toBeInTheDocument();
  });

  it("renders skeleton when loading=true", () => {
    const { container } = render(<MasteryGrid topics={[]} loading />);
    // Skeleton renders pulse elements
    expect(container.querySelectorAll("[class*='animate-pulse']").length).toBeGreaterThan(0);
  });
});

// ── SessionHistory ────────────────────────────────────────────────────────────
import { SessionHistory } from "../session-history";

const SESSION_ITEMS = [
  {
    id: "s1",
    date: "2026-07-10",
    mode: "quick_practice",
    topic: "integration_basics",
    duration_minutes: 12,
    delta_readiness: 2,
  },
  {
    id: "s2",
    date: "2026-07-09",
    mode: "explain",
    topic: null,
    duration_minutes: 0,
    delta_readiness: 0,
  },
];

describe("SessionHistory", () => {
  it("renders session rows", () => {
    render(<SessionHistory items={SESSION_ITEMS} />);
    expect(screen.getByText("Quick Practice")).toBeInTheDocument();
    expect(screen.getByText("12m")).toBeInTheDocument();
  });

  it("shows empty state when no sessions", () => {
    render(<SessionHistory items={[]} />);
    expect(screen.getByText(/session history will appear/i)).toBeInTheDocument();
  });

  it("shows +delta pill for positive delta", () => {
    render(<SessionHistory items={SESSION_ITEMS} />);
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("shows dash for missing topic", () => {
    render(<SessionHistory items={SESSION_ITEMS} />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});

// ── MarkerHistoryCompact ──────────────────────────────────────────────────────
import { MarkerHistoryCompact } from "../marker-history-compact";

const MARKER_ITEMS = [
  {
    id: "m1",
    date: "2026-07-08",
    marks: 4,
    max_marks: 6,
    delta_readiness: 2,
  },
  {
    id: "m2",
    date: "2026-07-07",
    marks: null,
    max_marks: 5,
    delta_readiness: 0,
  },
];

describe("MarkerHistoryCompact", () => {
  it("renders marks/max_marks", () => {
    render(<MarkerHistoryCompact items={MARKER_ITEMS} />);
    expect(screen.getByText("4/6")).toBeInTheDocument();
  });

  it("renders link to submission detail", () => {
    const { container } = render(<MarkerHistoryCompact items={MARKER_ITEMS} />);
    const links = container.querySelectorAll("a");
    expect(links[0]).toHaveAttribute("href", "/mark/m1");
  });

  it("shows empty state when items is empty", () => {
    render(<MarkerHistoryCompact items={[]} />);
    expect(screen.getByText(/submit a marked question/i)).toBeInTheDocument();
  });
});

// ── WeeklyStats ───────────────────────────────────────────────────────────────
import { WeeklyStats } from "../weekly-stats";

const STATS = {
  sessions_this_week: 4,
  questions_attempted: 47,
  marks_scored: 198,
  marks_max: 240,
  time_in_app_minutes: 138,
};

describe("WeeklyStats", () => {
  it("renders all four stat cells", () => {
    render(<WeeklyStats stats={STATS} />);
    expect(screen.getByText("4")).toBeInTheDocument();          // sessions
    expect(screen.getByText("47")).toBeInTheDocument();         // questions
    expect(screen.getByText("Sessions")).toBeInTheDocument();
    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText("Time in app")).toBeInTheDocument();
  });

  it("formats marks as 'scored of max'", () => {
    render(<WeeklyStats stats={STATS} />);
    expect(screen.getByText("198 of 240")).toBeInTheDocument();
  });

  it("formats minutes >= 60 as hours+minutes", () => {
    render(<WeeklyStats stats={STATS} />);
    // 138 min = 2h 18m
    expect(screen.getByText("2h 18m")).toBeInTheDocument();
  });

  it("formats minutes < 60 as plain minutes", () => {
    render(<WeeklyStats stats={{ ...STATS, time_in_app_minutes: 45 }} />);
    expect(screen.getByText("45m")).toBeInTheDocument();
  });
});
