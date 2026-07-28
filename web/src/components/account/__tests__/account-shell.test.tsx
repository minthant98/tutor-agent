import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AccountShell } from "../account-shell";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// next/navigation — AccountShell uses useSearchParams and useRouter
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn() }),
}));

// accountApi — prevent real fetch in tests
vi.mock("@/lib/api/account", () => ({
  accountApi: {
    get: vi.fn().mockResolvedValue({
      profile: { name: "Alex", email: "alex@example.com" },
      subjects: [],
      preferences: {
        worked_examples: true,
        visual: false,
        step_by_step: true,
        practice: false,
      },
      billing: { tier: "free", status: "active" },
    }),
  },
}));

// next-themes — ThemeSection uses useTheme
vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

// @/lib/theme-provider — re-export useTheme
vi.mock("@/lib/theme-provider", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AccountShell", () => {
  it("renders sections in fixed order", () => {
    render(<AccountShell />);
    const links = screen.getAllByRole("link").map((l) => l.textContent);
    expect(links).toEqual([
      "Profile",
      "Subjects",
      "Notifications",
      "Theme",
      "Keyboard Shortcuts",
      "Feedback",
      "Sign Out",
    ]);
  });

  it("marks Profile as the default active section", () => {
    render(<AccountShell />);
    const profileLink = screen.getByRole("link", { name: "Profile" });
    expect(profileLink).toHaveAttribute("aria-current", "page");
  });
});
