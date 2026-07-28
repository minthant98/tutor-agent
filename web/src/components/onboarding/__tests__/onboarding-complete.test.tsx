import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OnboardingComplete } from "../onboarding-complete";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe("OnboardingComplete", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders 'You're set.' heading", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    expect(
      screen.getByRole("heading", { name: /You're set\./i })
    ).toBeInTheDocument();
  });

  it("renders plan meta with minutes and segments", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    expect(screen.getByText(/22 minutes/)).toBeInTheDocument();
    expect(screen.getByText(/3 segments/)).toBeInTheDocument();
  });

  it("renders the Alex framing line about the roadmap", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    expect(screen.getByText(/Your roadmap is ready/)).toBeInTheDocument();
  });

  it("clicking 'Go to today's session' calls router.push", async () => {
    const user = userEvent.setup();
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    await user.click(screen.getByRole("button", { name: /Go to today's session/i }));
    expect(mockPush).toHaveBeenCalledWith("/sessions/today");
  });

  it("uses sessionHref when provided", async () => {
    const user = userEvent.setup();
    render(
      <OnboardingComplete
        plan={{ minutes: 30, segments: 4, sessionHref: "/session/abc123" }}
      />
    );
    await user.click(screen.getByRole("button", { name: /Go to today's session/i }));
    expect(mockPush).toHaveBeenCalledWith("/session/abc123");
  });

  it("does not contain celebratory copy", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    const text = document.body.textContent!.toLowerCase();
    const banned = ["welcome", "congratulations", "yay", "amazing"];
    for (const b of banned) {
      expect(text).not.toContain(b);
    }
  });

  it("does not contain exclamation marks", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    expect(document.body.textContent).not.toContain("!");
  });

  it("does not contain emoji", () => {
    render(<OnboardingComplete plan={{ minutes: 22, segments: 3 }} />);
    // Check for 🎉 and other common celebration emoji
    expect(document.body.textContent).not.toContain("🎉");
    expect(document.body.textContent).not.toContain("🎊");
    expect(document.body.textContent).not.toContain("🥳");
  });
});
