import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockRouterPush = vi.fn();

// We'll swap useSearchParams per test by controlling this factory.
let searchParamsFactory: () => URLSearchParams = () => new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockRouterPush }),
  useSearchParams: () => searchParamsFactory(),
}));

vi.mock("@/hooks/use-current-subject", () => ({
  useCurrentSubject: () => ({ subject: "maths" }),
}));

vi.mock("@/lib/api/practice", () => ({
  practiceApi: {
    getPlan: vi.fn(),
    startSession: vi.fn(),
  },
}));

// Stub PlannerTransparency so the Start button is easy to click.
vi.mock("@/components/practice/planner-transparency", () => ({
  PlannerTransparency: ({
    onStart,
  }: {
    onStart: () => void;
    onChangeMode: () => void;
    narration: string;
    segments: unknown[];
    minutes: number;
  }) => (
    <button type="button" onClick={onStart}>
      Start
    </button>
  ),
}));

// ── Imports (after mocks) ─────────────────────────────────────────────────────

import PracticePlanPage from "../page";
import { practiceApi } from "@/lib/api/practice";

const mockedGetPlan = vi.mocked(practiceApi.getPlan);
const mockedStartSession = vi.mocked(practiceApi.startSession);

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
  mockedGetPlan.mockResolvedValue({
    narration: "Let's practise substitution.",
    segments: [{ intent: "teach", topic: "Substitution" }],
    minutes: 10,
  });
  mockedStartSession.mockResolvedValue({ session_id: "sess-abc", message: "ok", is_new_student: false });
});

describe("PracticePlanPage — source_submission_id forwarding", () => {
  it("passes source_submission_id to startSession when submission_id is in URL", async () => {
    const user = userEvent.setup();
    const SUB_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890";

    searchParamsFactory = () =>
      new URLSearchParams(
        `mode=drill_in&topic=integration_basics&skill=substitution&submission_id=${SUB_ID}`
      );

    render(<PracticePlanPage />);

    // Wait for the plan to load and the Start button to appear.
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Start/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Start/ }));

    expect(mockedStartSession).toHaveBeenCalledWith(
      "maths",
      "drill_in",
      "integration_basics",
      "substitution",
      SUB_ID
    );
  });

  it("calls startSession without source_submission_id when no submission_id in URL", async () => {
    const user = userEvent.setup();

    searchParamsFactory = () =>
      new URLSearchParams("mode=drill_in&topic=integration_basics&skill=substitution");

    render(<PracticePlanPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Start/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Start/ }));

    expect(mockedStartSession).toHaveBeenCalledWith(
      "maths",
      "drill_in",
      "integration_basics",
      "substitution",
      null
    );
  });
});
