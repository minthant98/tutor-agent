import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SessionComplete } from "../session-complete";

// Mock next/link to avoid Next.js router requirement in tests
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

describe("SessionComplete", () => {
  it("renders title, duration, segment count, and readiness", () => {
    render(
      <SessionComplete
        totalMinutes={22}
        segmentCount={3}
        readinessAfter={71}
      />
    );

    expect(
      screen.getByRole("heading", { name: /Today's Session Complete/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/22/)).toBeInTheDocument();
    expect(screen.getByText(/3/)).toBeInTheDocument();
    expect(screen.getByText(/71%/)).toBeInTheDocument();
  });

  it("renders progress link and back-to-home link", () => {
    render(
      <SessionComplete
        totalMinutes={22}
        segmentCount={3}
        readinessAfter={71}
      />
    );

    expect(
      screen.getByRole("link", { name: /Review your progress/i })
    ).toHaveAttribute("href", "/progress");
    expect(
      screen.getByRole("link", { name: /Back to home/i })
    ).toHaveAttribute("href", "/");
  });

  it("does not include praise words", () => {
    render(
      <SessionComplete
        totalMinutes={22}
        segmentCount={3}
        readinessAfter={71}
      />
    );
    const text = screen.getByRole("region").textContent!.toLowerCase();

    for (const banned of [
      "great job",
      "well done",
      "amazing",
      "congrats",
      "🎉",
      "!",
    ]) {
      expect(text).not.toContain(banned);
    }
  });

  it("readiness line does not have any animate class", () => {
    render(
      <SessionComplete
        totalMinutes={22}
        segmentCount={3}
        readinessAfter={71}
      />
    );

    // Find element containing the readiness percentage
    const readinessEl = screen.getByText(/71%/);
    // Neither the element itself nor its parent should have animate-* classes
    expect(readinessEl.className).not.toMatch(/animate/);
    const parent = readinessEl.parentElement;
    if (parent) {
      expect(parent.className).not.toMatch(/animate/);
    }
  });

  it("rounds fractional readiness to whole percent", () => {
    render(
      <SessionComplete
        totalMinutes={15}
        segmentCount={2}
        readinessAfter={71.7}
      />
    );
    expect(screen.getByText(/72%/)).toBeInTheDocument();
  });

  it("has role=region with accessible label", () => {
    render(
      <SessionComplete
        totalMinutes={22}
        segmentCount={3}
        readinessAfter={71}
      />
    );
    expect(screen.getByRole("region", { name: /Session complete/i })).toBeInTheDocument();
  });
});
