import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AlexDrawer } from "../alex-drawer";

// ── Mocks ──────────────────────────────────────────────────────────────────

// Mock the hook so we don't need real API calls
vi.mock("@/hooks/use-alex-session", () => ({
  useAlexSession: () => ({
    messages: [],
    send: vi.fn(),
    isStreaming: false,
  }),
}));

// Mock useKeyboardShortcut so we can control key events via keyboard handler
// We let the real implementation run (it uses document.addEventListener)
// but we mock the module to keep control.
vi.mock("@/hooks/use-keyboard-shortcut", () => ({
  useKeyboardShortcut: (
    combo: string,
    handler: () => void,
    _opts?: object
  ) => {
    // Register on window for the test to dispatch
    if (typeof window !== "undefined") {
      const onKey = (e: KeyboardEvent) => {
        const parts = combo.toLowerCase().split("+");
        const key = parts.pop()!;
        const wantMeta = parts.includes("cmd") || parts.includes("ctrl");
        if (
          e.key.toLowerCase() === key &&
          (!wantMeta || e.metaKey || e.ctrlKey)
        ) {
          e.preventDefault();
          handler();
        }
      };
      document.addEventListener("keydown", onKey);
      // Cleanup is handled by the component's useEffect teardown;
      // here we just register so events work in tests.
    }
  },
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function renderDrawer() {
  return render(<AlexDrawer sessionId="session-123" />);
}

function fireMetaKey(key: string) {
  document.dispatchEvent(
    new KeyboardEvent("keydown", {
      key,
      metaKey: true,
      bubbles: true,
    })
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("AlexDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("is closed by default", () => {
    renderDrawer();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens on ⌘/", async () => {
    renderDrawer();
    act(() => {
      fireMetaKey("/");
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("opens on ⌘J", async () => {
    renderDrawer();
    act(() => {
      fireMetaKey("j");
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("opens on stride:open-alex-drawer event", async () => {
    renderDrawer();
    act(() => {
      window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("Esc closes the drawer", async () => {
    const user = userEvent.setup();
    renderDrawer();

    // Open first
    act(() => {
      window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();

    // Esc should close it (Radix Dialog handles this)
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows suggestion chips when no messages", async () => {
    renderDrawer();
    act(() => {
      window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
    });
    await screen.findByRole("dialog");
    expect(screen.getByText("Explain the current step")).toBeInTheDocument();
    expect(screen.getByText("Give me a similar example")).toBeInTheDocument();
    expect(screen.getByText("What did I miss?")).toBeInTheDocument();
  });

  it("renders the Alex title in the header", async () => {
    renderDrawer();
    act(() => {
      window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
    });
    await screen.findByRole("dialog");
    expect(screen.getByText("Alex")).toBeInTheDocument();
  });

  it("has a message input textarea", async () => {
    renderDrawer();
    act(() => {
      window.dispatchEvent(new CustomEvent("stride:open-alex-drawer"));
    });
    await screen.findByRole("dialog");
    expect(
      screen.getByPlaceholderText("Ask about the current question…")
    ).toBeInTheDocument();
  });
});
