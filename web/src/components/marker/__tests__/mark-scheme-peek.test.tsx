import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { MarkSchemePeek } from "../mark-scheme-peek";

describe("MarkSchemePeek", () => {
  it("mark scheme hidden by default", () => {
    render(<MarkSchemePeek scheme="M1 A1..." onEventPreReveal={vi.fn()} />);
    expect(screen.getByText(/Available after submission/)).toBeInTheDocument();
    expect(screen.queryByText("M1 A1...")).not.toBeInTheDocument();
  });

  it("Reveal opens confirm dialog", async () => {
    const user = userEvent.setup();
    render(<MarkSchemePeek scheme="M1 A1..." onEventPreReveal={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Reveal anyway/ }));
    expect(
      await screen.findByText(/may reduce the value of this practice session/)
    ).toBeInTheDocument();
  });

  it("Confirm reveals scheme and fires event", async () => {
    const user = userEvent.setup();
    const onEvent = vi.fn();
    render(<MarkSchemePeek scheme="M1 A1..." onEventPreReveal={onEvent} />);
    await user.click(screen.getByRole("button", { name: /Reveal anyway/ }));
    await user.click(screen.getByRole("button", { name: "Reveal" }));
    expect(screen.getByText("M1 A1...")).toBeInTheDocument();
    expect(onEvent).toHaveBeenCalled();
  });

  it("Cancel keeps scheme hidden", async () => {
    const user = userEvent.setup();
    render(<MarkSchemePeek scheme="M1 A1..." onEventPreReveal={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Reveal anyway/ }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText("M1 A1...")).not.toBeInTheDocument();
    expect(screen.getByText(/Available after submission/)).toBeInTheDocument();
  });
});
