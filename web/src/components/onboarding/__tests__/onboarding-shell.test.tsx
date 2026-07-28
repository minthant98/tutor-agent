import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { OnboardingShell } from "../onboarding-shell";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
}));

// Mock useKeyboardShortcut — it calls document.addEventListener which is fine
// in jsdom, but let's ensure it doesn't error.
vi.mock("@/hooks/use-keyboard-shortcut", () => ({
  useKeyboardShortcut: vi.fn(),
}));

describe("OnboardingShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 6 dots in the progress rail", () => {
    render(
      <OnboardingShell currentStep={0} alexLine="Alex needs to know your syllabus.">
        <div>step content</div>
      </OnboardingShell>
    );

    const dots = screen.getAllByRole("listitem");
    expect(dots).toHaveLength(6);
  });

  it("marks current step dot with aria-current='step'", () => {
    render(
      <OnboardingShell currentStep={2} alexLine="Some framing">
        <div />
      </OnboardingShell>
    );

    const dots = screen.getAllByRole("listitem");
    // Dots are 0-indexed; step index 2 → third dot
    expect(dots[2]).toHaveAttribute("aria-current", "step");
  });

  it("does not set aria-current on non-current dots", () => {
    render(
      <OnboardingShell currentStep={1} alexLine="Some framing">
        <div />
      </OnboardingShell>
    );

    const dots = screen.getAllByRole("listitem");
    expect(dots[0]).not.toHaveAttribute("aria-current");
    expect(dots[2]).not.toHaveAttribute("aria-current");
  });

  it("renders the Alex analytical framing line above the step content", () => {
    render(
      <OnboardingShell
        currentStep={0}
        alexLine="Alex needs to know your syllabus before it can plan sessions."
      >
        <div>step</div>
      </OnboardingShell>
    );

    expect(
      screen.getByText(/Alex needs to know your syllabus/)
    ).toBeInTheDocument();
  });

  it("hides Back button on step 0", () => {
    render(
      <OnboardingShell currentStep={0} alexLine="Line">
        <div />
      </OnboardingShell>
    );

    expect(screen.queryByRole("button", { name: /back/i })).not.toBeInTheDocument();
  });

  it("shows Back button on step > 0", () => {
    render(
      <OnboardingShell currentStep={1} alexLine="Line">
        <div />
      </OnboardingShell>
    );

    expect(screen.getByRole("button", { name: /back/i })).toBeInTheDocument();
  });

  it("disables Continue when canContinue is false", () => {
    render(
      <OnboardingShell currentStep={0} alexLine="Line" canContinue={false}>
        <div />
      </OnboardingShell>
    );

    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
  });

  it("renders the optional heading", () => {
    render(
      <OnboardingShell
        currentStep={0}
        alexLine="Line"
        heading="Which subjects?"
      >
        <div />
      </OnboardingShell>
    );

    expect(
      screen.getByRole("heading", { name: "Which subjects?" })
    ).toBeInTheDocument();
  });
});
