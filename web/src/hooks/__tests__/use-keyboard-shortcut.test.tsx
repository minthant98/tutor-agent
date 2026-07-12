import { renderHook } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { useKeyboardShortcut } from "../use-keyboard-shortcut";

describe("useKeyboardShortcut", () => {
  it("fires on matching key combo", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut("Cmd+H", handler));
    await user.keyboard("{Meta>}h{/Meta}");
    expect(handler).toHaveBeenCalledOnce();
  });

  it("does not fire when typing in an input", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    renderHook(() => useKeyboardShortcut("Cmd+H", handler));
    await user.keyboard("{Meta>}h{/Meta}");
    expect(handler).not.toHaveBeenCalled();
    input.remove();
  });

  it("fires on Ctrl+H (equivalent to Cmd+H)", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut("Cmd+H", handler));
    await user.keyboard("{Control>}h{/Control}");
    expect(handler).toHaveBeenCalledOnce();
  });

  it("fires on plain key like ?", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut("?", handler));
    await user.keyboard("?");
    expect(handler).toHaveBeenCalledOnce();
  });

  it("fires with ignoreInInput: false even when input is focused", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    renderHook(() => useKeyboardShortcut("Cmd+H", handler, { ignoreInInput: false }));
    await user.keyboard("{Meta>}h{/Meta}");
    expect(handler).toHaveBeenCalledOnce();
    input.remove();
  });

  it("fires on Cmd+Shift+M", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcut("Cmd+Shift+M", handler));
    await user.keyboard("{Meta>}{Shift>}m{/Shift}{/Meta}");
    expect(handler).toHaveBeenCalledOnce();
  });
});
