import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { HistoryFilters } from "../history-filters";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(),
}));

beforeEach(() => {
  mockPush.mockClear();
});

describe("HistoryFilters", () => {
  it("renders Difficulty label", () => {
    render(<HistoryFilters />);
    expect(screen.getByText("Difficulty")).toBeInTheDocument();
  });

  it("renders all difficulty options", () => {
    render(<HistoryFilters />);
    expect(screen.getByRole("radio", { name: "Any" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "≤3 marks" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "4–6" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "7+" })).toBeInTheDocument();
  });

  it("renders all status options", () => {
    render(<HistoryFilters />);
    expect(screen.getByRole("radio", { name: "All" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Graded" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Error" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Pending" })).toBeInTheDocument();
  });

  it("selecting Difficulty 4-6 updates URL with difficulty=medium", async () => {
    const user = userEvent.setup();
    render(<HistoryFilters />);
    await user.click(screen.getByRole("radio", { name: "4–6" }));
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringMatching(/difficulty=medium/)
    );
  });

  it("selecting Difficulty 7+ updates URL with difficulty=hard", async () => {
    const user = userEvent.setup();
    render(<HistoryFilters />);
    await user.click(screen.getByRole("radio", { name: "7+" }));
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringMatching(/difficulty=hard/)
    );
  });

  it("selecting Difficulty ≤3 marks updates URL with difficulty=easy", async () => {
    const user = userEvent.setup();
    render(<HistoryFilters />);
    await user.click(screen.getByRole("radio", { name: "≤3 marks" }));
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringMatching(/difficulty=easy/)
    );
  });

  it("selecting Status Graded updates URL with status=graded", async () => {
    const user = userEvent.setup();
    render(<HistoryFilters />);
    await user.click(screen.getByRole("radio", { name: "Graded" }));
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringMatching(/status=graded/)
    );
  });
});
