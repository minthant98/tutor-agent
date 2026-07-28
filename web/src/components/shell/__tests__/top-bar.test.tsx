import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { TopBar } from "../top-bar";
import { Breadcrumb } from "../breadcrumb";

vi.mock("next/navigation", () => ({ usePathname: () => "/practice" }));

vi.mock("../../../hooks/use-current-subject", () => ({
  useCurrentSubject: () => ({
    subject: "pure_mathematics",
    subjects: [{ id: "pure_mathematics", label: "Pure Mathematics" }],
    setSubject: vi.fn(),
  }),
}));

describe("TopBar", () => {
  it('renders breadcrumb "Practice" when pathname="/practice"', () => {
    render(<TopBar />);
    expect(screen.getByText("Practice")).toBeInTheDocument();
  });

  it("Ask Alex button dispatches stride:open-alex-drawer", async () => {
    const user = userEvent.setup();
    const spy = vi.fn();
    window.addEventListener("stride:open-alex-drawer", spy);
    render(<TopBar />);
    await user.click(screen.getByRole("button", { name: /ask alex/i }));
    expect(spy).toHaveBeenCalledOnce();
    window.removeEventListener("stride:open-alex-drawer", spy);
  });

  it("Search icon dispatches stride:open-cmdk", async () => {
    const user = userEvent.setup();
    const spy = vi.fn();
    window.addEventListener("stride:open-cmdk", spy);
    render(<TopBar />);
    await user.click(screen.getByRole("button", { name: /search/i }));
    expect(spy).toHaveBeenCalledOnce();
    window.removeEventListener("stride:open-cmdk", spy);
  });

  it("Subject switcher renders label from hook (never hardcoded)", () => {
    render(<TopBar />);
    expect(screen.getByText("Pure Mathematics")).toBeInTheDocument();
  });

  it("Avatar is hidden on desktop (has md:hidden class)", () => {
    render(<TopBar />);
    const avatar = document.querySelector("[data-testid='topbar-avatar']");
    expect(avatar).not.toBeNull();
    expect(avatar?.className).toContain("md:hidden");
  });
});

describe("Breadcrumb", () => {
  it('renders "Practice / Plan" for nested pathname "/practice/plan"', () => {
    render(<Breadcrumb pathname="/practice/plan" />);
    expect(screen.getByText("Practice")).toBeInTheDocument();
    expect(screen.getByText("Plan")).toBeInTheDocument();
  });

  it('renders "Practice" for pathname "/practice"', () => {
    render(<Breadcrumb pathname="/practice" />);
    expect(screen.getByText("Practice")).toBeInTheDocument();
  });

  it('renders "Home" for root pathname "/"', () => {
    render(<Breadcrumb pathname="/" />);
    expect(screen.getByText("Home")).toBeInTheDocument();
  });
});
