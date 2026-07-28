import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AlexObservations } from "../alex-observations";
import * as useObservationsModule from "@/hooks/use-observations";

// Mock the hook so we can control what it returns
vi.mock("@/hooks/use-observations", () => ({
  useObservations: vi.fn(),
}));

const mockUseObservations = vi.mocked(useObservationsModule.useObservations);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AlexObservations", () => {
  it("renders nothing when observation list is empty", () => {
    mockUseObservations.mockReturnValue({
      observations: [],
      isLoading: false,
      error: null,
    });

    const { container } = render(<AlexObservations subject="pure_mathematics" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing while loading", () => {
    mockUseObservations.mockReturnValue({
      observations: [],
      isLoading: true,
      error: null,
    });

    const { container } = render(<AlexObservations subject="pure_mathematics" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing on error", () => {
    mockUseObservations.mockReturnValue({
      observations: [],
      isLoading: false,
      error: new Error("fetch failed"),
    });

    const { container } = render(<AlexObservations subject="pure_mathematics" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders header and 2 bullets when 2 observations returned", () => {
    mockUseObservations.mockReturnValue({
      observations: [
        {
          id: "obs-1",
          text: "Integration mastery dropped 12% this week.",
          computed_at: "2026-07-07T10:00:00Z",
        },
        {
          id: "obs-2",
          text: "Two sessions covered calculus but no graded upload was submitted.",
          computed_at: "2026-07-07T10:00:01Z",
        },
      ],
      isLoading: false,
      error: null,
    });

    render(<AlexObservations subject="pure_mathematics" />);

    // Header visible
    expect(screen.getByText("What Alex noticed this week")).toBeInTheDocument();

    // Both observation texts visible
    expect(
      screen.getByText(/Integration mastery dropped 12%/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Two sessions covered calculus/)
    ).toBeInTheDocument();
  });

  it("caps at 3 bullets even when hook returns more", () => {
    mockUseObservations.mockReturnValue({
      observations: [
        { id: "1", text: "Observation one.", computed_at: "2026-07-07T10:00:00Z" },
        { id: "2", text: "Observation two.", computed_at: "2026-07-07T10:00:01Z" },
        { id: "3", text: "Observation three.", computed_at: "2026-07-07T10:00:02Z" },
        { id: "4", text: "Observation four — should not render.", computed_at: "2026-07-07T10:00:03Z" },
      ],
      isLoading: false,
      error: null,
    });

    render(<AlexObservations subject="pure_mathematics" />);

    expect(screen.queryByText(/Observation four/)).not.toBeInTheDocument();
    expect(screen.getByText("Observation one.")).toBeInTheDocument();
    expect(screen.getByText("Observation three.")).toBeInTheDocument();
  });
});
