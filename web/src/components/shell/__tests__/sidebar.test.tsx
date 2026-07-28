import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Sidebar } from "../sidebar";

vi.mock("next/navigation", () => ({ usePathname: () => "/practice" }));
vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode; [key: string]: unknown }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));
vi.mock("../../../hooks/use-active-session", () => ({
  useActiveSession: () => null,
}));

describe("Sidebar", () => {
  it("renders all five primary nav items", () => {
    render(<Sidebar />);
    expect(screen.getByRole("link", { name: /home/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /practice/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /exam marker/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /topics/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /progress/i })).toBeInTheDocument();
  });

  it("marks Practice as active based on pathname", () => {
    render(<Sidebar />);
    const practiceLink = screen.getByRole("link", { name: /practice/i });
    expect(practiceLink).toHaveAttribute("aria-current", "page");
  });

  it("home link does not get active state for /practice pathname", () => {
    render(<Sidebar />);
    const homeLink = screen.getByRole("link", { name: /home/i });
    expect(homeLink).not.toHaveAttribute("aria-current", "page");
  });

  it("does not show Continue pill when no active session", () => {
    render(<Sidebar />);
    expect(screen.queryByText(/continue/i)).not.toBeInTheDocument();
  });

  it("has aria-label Primary on the nav element", () => {
    render(<Sidebar />);
    expect(screen.getByRole("navigation", { name: /primary/i })).toBeInTheDocument();
  });
});
