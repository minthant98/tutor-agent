import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { CmdK } from "../cmd-k";

// Mock Next.js navigation hooks
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/",
}));

// Mock the search hook to avoid real fetch calls in unit tests
vi.mock("../../../hooks/use-cmd-k", () => ({
  useSearchResults: () => ({
    topics: [],
    recent: [],
    navigate: [],
    isLoading: false,
    error: null,
  }),
}));

describe("CmdK", () => {
  beforeEach(() => {
    // Ensure a clean DOM for each test
    document.documentElement.className = "";
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("opens on ⌘K", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    // Dialog should not be visible initially
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    // Press Cmd+K
    await user.keyboard("{Meta>}k{/Meta}");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("shows Actions section by default", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    await user.keyboard("{Meta>}k{/Meta}");
    expect(await screen.findByText(/actions/i)).toBeInTheDocument();
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    // Open it first
    await user.keyboard("{Meta>}k{/Meta}");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    // Close with Escape
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens via stride:open-cmdk custom event", async () => {
    render(<CmdK />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await act(async () => {
      window.dispatchEvent(new CustomEvent("stride:open-cmdk"));
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("toggles closed on second ⌘K press while open", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    await user.keyboard("{Meta>}k{/Meta}");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    await user.keyboard("{Meta>}k{/Meta}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows static action items when open", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    await user.keyboard("{Meta>}k{/Meta}");
    // These come from ACTIONS in cmd-k-index.ts
    expect(await screen.findByText("Start Today's Session")).toBeInTheDocument();
    expect(screen.getByText("Open Exam Marker")).toBeInTheDocument();
    expect(screen.getByText("Ask Alex")).toBeInTheDocument();
    expect(screen.getByText("Start Practice")).toBeInTheDocument();
  });

  it("shows Account section when open", async () => {
    const user = userEvent.setup();
    render(<CmdK />);
    await user.keyboard("{Meta>}k{/Meta}");
    expect(await screen.findByText(/account/i)).toBeInTheDocument();
    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });
});
