import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AppShell } from "../app-shell";

// Mock sub-components — unit test focuses on flag gating and layout,
// not the internals of Sidebar / TopBar / CmdK / ShortcutHelp.
vi.mock("../sidebar", () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));
vi.mock("../top-bar", () => ({
  TopBar: () => <div data-testid="topbar" />,
}));
vi.mock("../cmd-k", () => ({
  CmdK: () => <div data-testid="cmdk" />,
}));
vi.mock("../shortcut-help", () => ({
  ShortcutHelp: () => <div data-testid="shortcut-help" />,
}));

// Mock Next.js navigation (used by Sidebar, TopBar sub-components in real code)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/",
}));

// Mock feature flags so we can control the flag value per test
vi.mock("@/lib/feature-flags", () => ({
  useFeatureFlag: vi.fn(),
}));

import { useFeatureFlag } from "@/lib/feature-flags";
const mockUseFeatureFlag = vi.mocked(useFeatureFlag);

describe("AppShell", () => {
  it("renders children unchanged when shell_v3 is off", () => {
    mockUseFeatureFlag.mockReturnValue(false);
    render(
      <AppShell>
        <div data-testid="page-content">Hello</div>
      </AppShell>
    );
    expect(screen.getByTestId("page-content")).toBeInTheDocument();
    expect(screen.queryByTestId("sidebar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("topbar")).not.toBeInTheDocument();
  });

  it("renders full shell when shell_v3 is on", () => {
    mockUseFeatureFlag.mockReturnValue(true);
    render(
      <AppShell>
        <div data-testid="page-content">Hello</div>
      </AppShell>
    );
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("topbar")).toBeInTheDocument();
    expect(screen.getByTestId("cmdk")).toBeInTheDocument();
    expect(screen.getByTestId("shortcut-help")).toBeInTheDocument();
    expect(screen.getByTestId("page-content")).toBeInTheDocument();
  });
});
