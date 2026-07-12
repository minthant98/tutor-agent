import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { ShortcutHelp } from "../shortcut-help";

describe("ShortcutHelp", () => {
  it("opens on ?", async () => {
    const user = userEvent.setup();
    render(<ShortcutHelp />);
    await user.keyboard("?");
    expect(
      await screen.findByRole("dialog", { name: /keyboard shortcuts/i })
    ).toBeInTheDocument();
  });

  it("lists ⌘K", async () => {
    const user = userEvent.setup();
    render(<ShortcutHelp />);
    await user.keyboard("?");
    // Multiple ⌘K entries (Global + Cmd-K group); just verify at least one exists
    const matches = await screen.findAllByText("⌘K");
    expect(matches.length).toBeGreaterThan(0);
  });

  it("renders all shortcut groups", async () => {
    const user = userEvent.setup();
    render(<ShortcutHelp />);
    await user.keyboard("?");
    await screen.findByRole("dialog");
    expect(screen.getByText("Global")).toBeInTheDocument();
    expect(screen.getByText("Session")).toBeInTheDocument();
    expect(screen.getByText("Marker")).toBeInTheDocument();
    expect(screen.getByText("Alex")).toBeInTheDocument();
    expect(screen.getByText("Cmd-K")).toBeInTheDocument();
  });

  it("does not open if ? is pressed while an input is focused", async () => {
    const user = userEvent.setup();
    render(<ShortcutHelp />);
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    await user.keyboard("?");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    input.remove();
  });
});
