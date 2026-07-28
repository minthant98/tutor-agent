import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import TargetGradeStep from "../page";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
}));

vi.mock("posthog-js", () => ({
  default: { capture: vi.fn() },
}));

vi.mock("@/lib/api/onboarding", () => ({
  onboardingApi: {
    submitTargetGrade: vi.fn(),
    getState: vi.fn(),
  },
}));

vi.mock("@/components/onboarding/wizard-shell", () => ({
  WizardShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="wizard-shell">{children}</div>
  ),
}));

vi.mock("@/components/onboarding/onboarding-shell", () => ({
  OnboardingShell: ({
    children,
    onContinue,
    canContinue,
  }: {
    children: React.ReactNode;
    onContinue?: () => void;
    canContinue?: boolean;
  }) => (
    <div data-testid="onboarding-shell">
      {children}
      <button onClick={onContinue} disabled={!canContinue}>
        Continue
      </button>
    </div>
  ),
}));

vi.mock("@/components/onboarding/fields/grade-picker", () => ({
  GradePicker: ({ onChange }: { onChange: (g: string) => void }) => (
    <button onClick={() => onChange("A")}>Pick A</button>
  ),
}));

// ── Feature flag mock — will be overridden per-test ───────────────────────

const mockUseFeatureFlag = vi.fn();

vi.mock("@/lib/feature-flags", () => ({
  useFeatureFlag: (...args: unknown[]) => mockUseFeatureFlag(...args),
}));

// ── Imports after mocks ────────────────────────────────────────────────────

import { onboardingApi } from "@/lib/api/onboarding";

const mockedSubmitTargetGrade = vi.mocked(onboardingApi.submitTargetGrade);
const mockedGetState = vi.mocked(onboardingApi.getState);

// ── Tests ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
  mockedSubmitTargetGrade.mockResolvedValue(undefined as never);
});

describe("TargetGradeStep — v3 routing", () => {
  it("routes to /onboarding/preferences after saving in v3 mode", async () => {
    // Arrange: v3 flag enabled
    mockUseFeatureFlag.mockReturnValue(true);

    const user = userEvent.setup();
    render(<TargetGradeStep />);

    // Pick a grade to enable Continue
    await user.click(screen.getByText("Pick A"));

    // Act: click Continue
    await user.click(screen.getByRole("button", { name: /continue/i }));

    // Assert: routes to preferences, NOT assessment
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/onboarding/preferences");
    });
    expect(mockPush).not.toHaveBeenCalledWith(
      expect.stringContaining("assessment")
    );
    // getState should NOT be called in v3 path
    expect(mockedGetState).not.toHaveBeenCalled();
  });
});

describe("TargetGradeStep — v2 routing (unchanged)", () => {
  it("maps preferences → assessment via getState in v2 mode", async () => {
    // Arrange: v3 flag disabled
    mockUseFeatureFlag.mockReturnValue(false);
    mockedGetState.mockResolvedValue({ next_step: "preferences" } as never);

    const user = userEvent.setup();
    render(<TargetGradeStep />);

    // Pick a grade and submit via the v2 Continue button rendered inside WizardShell
    await user.click(screen.getByText("Pick A"));
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/onboarding/assessment");
    });
  });

  it("follows getState next_step directly when it is not 'preferences' in v2 mode", async () => {
    mockUseFeatureFlag.mockReturnValue(false);
    mockedGetState.mockResolvedValue({ next_step: "exam-date" } as never);

    const user = userEvent.setup();
    render(<TargetGradeStep />);

    await user.click(screen.getByText("Pick A"));
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/onboarding/exam-date");
    });
  });
});
