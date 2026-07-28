import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ActionBar } from "../action-bar";

describe("ActionBar", () => {
  it("center is always the primary", () => {
    render(<ActionBar primary={{ label: "Continue", onClick: vi.fn() }} />);
    const primary = screen.getByRole("button", { name: "Continue" });
    expect(primary).toHaveAttribute("data-variant", "primary");
  });

  it("empty left slot preserves layout width", () => {
    const { container } = render(
      <ActionBar primary={{ label: "Start", onClick: vi.fn() }} />
    );
    const left = container.querySelector('[data-slot="left"]');
    expect(left).toBeInTheDocument();
    expect(left).not.toHaveClass("hidden");
  });

  it("renders Previous in left when provided", () => {
    render(
      <ActionBar
        left={{ label: "Previous", onClick: vi.fn() }}
        primary={{ label: "Next", onClick: vi.fn() }}
      />
    );
    expect(screen.getByRole("button", { name: "Previous" })).toBeInTheDocument();
  });

  it("renders Skip on the right when right prop provided", () => {
    render(
      <ActionBar
        primary={{ label: "Continue", onClick: vi.fn() }}
        right={{ label: "Skip", onClick: vi.fn() }}
      />
    );
    expect(screen.getByRole("button", { name: "Skip" })).toBeInTheDocument();
  });

  it("Enter key triggers primary onClick", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<ActionBar primary={{ label: "Continue", onClick }} />);
    await user.keyboard("{Enter}");
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders shortcut chip when primary.shortcut provided", () => {
    render(
      <ActionBar primary={{ label: "Continue", onClick: vi.fn(), shortcut: "↵" }} />
    );
    expect(screen.getByText("↵")).toBeInTheDocument();
  });
});
