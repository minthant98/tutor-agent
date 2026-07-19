import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TopicsV3Inner } from "../page";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/topics",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/topics", () => ({
  topicsApi: {
    getV3: vi.fn(),
  },
}));

// Mock TopicsGrid and TopicsFilters to keep tests focused on page behaviour.
vi.mock("@/components/topics/topics-grid", () => ({
  TopicsGrid: ({ topics }: { topics: unknown[] }) => (
    <div data-testid="topics-grid">{topics.length} topics</div>
  ),
}));

vi.mock("@/components/topics/topics-filters", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/components/topics/topics-filters")>();
  return {
    ...actual,
    TopicsFilters: () => <div data-testid="topics-filters" />,
    useTopicsFilters: () => ({
      filters: { status: [], recency: null },
      setStatus: vi.fn(),
      setRecency: vi.fn(),
      clearFilters: vi.fn(),
    }),
  };
});

// ── Tests ─────────────────────────────────────────────────────────────────────

import { topicsApi } from "@/lib/api/topics";

const mockedGetV3 = vi.mocked(topicsApi.getV3);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TopicsV3Inner — error state", () => {
  it("renders the error callout when fetch fails", async () => {
    mockedGetV3.mockRejectedValue(new Error("Network error"));

    render(<TopicsV3Inner subject="maths" />);

    await waitFor(() => {
      expect(
        screen.getByText(/Something went wrong loading topics\. Try again in a moment\./i)
      ).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
  });

  it("does NOT render the error message on successful fetch", async () => {
    mockedGetV3.mockResolvedValue([]);

    render(<TopicsV3Inner subject="maths" />);

    await waitFor(() => {
      expect(screen.getByTestId("topics-grid")).toBeInTheDocument();
    });

    expect(
      screen.queryByText(/Something went wrong loading topics/i)
    ).not.toBeInTheDocument();
  });

  it("re-fires the fetch when Retry is clicked", async () => {
    const user = userEvent.setup();
    mockedGetV3
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce([]);

    render(<TopicsV3Inner subject="maths" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Retry/i }));

    await waitFor(() => {
      expect(screen.getByTestId("topics-grid")).toBeInTheDocument();
    });

    expect(mockedGetV3).toHaveBeenCalledTimes(2);
  });
});
