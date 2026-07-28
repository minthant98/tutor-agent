import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { useAutosave } from "../use-autosave";

// Mock the auth module so getToken doesn't touch localStorage (which can
// behave unexpectedly when vi.useFakeTimers() replaces browser globals).
vi.mock("@/lib/auth", () => ({
  getToken: () => null,
}));

describe("useAutosave", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("PATCHes debounced state after 300ms", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue({ ok: true } as Response);

    const { rerender } = renderHook(
      ({ state }) => useAutosave({ sessionId: "s1", state }),
      {
        initialProps: { state: { cursor: { segment_index: 0, block_index: 0 } } },
      }
    );

    // Change state — this resets the debounce timer
    rerender({ state: { cursor: { segment_index: 0, block_index: 1 } } });

    // Timer hasn't fired yet
    expect(spy).not.toHaveBeenCalled();

    // Advance past debounce window
    act(() => {
      vi.advanceTimersByTime(310);
    });

    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/sessions/s1/state"),
      expect.objectContaining({ method: "PATCH" })
    );

    vi.useRealTimers();
  });

  it("does not PATCH within 300ms of the last change (debounce holds)", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue({ ok: true } as Response);

    const { rerender } = renderHook(
      ({ state }) => useAutosave({ sessionId: "s1", state }),
      {
        initialProps: { state: { cursor: { segment_index: 0, block_index: 0 } } },
      }
    );

    rerender({ state: { cursor: { segment_index: 0, block_index: 1 } } });

    act(() => {
      vi.advanceTimersByTime(200); // inside the 300ms window
    });

    expect(spy).not.toHaveBeenCalled();

    vi.useRealTimers();
  });

  it("sends only one PATCH (latest state) when changes arrive rapidly", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue({ ok: true } as Response);

    const { rerender } = renderHook(
      ({ state }) => useAutosave({ sessionId: "s1", state }),
      {
        initialProps: { state: { cursor: { segment_index: 0, block_index: 0 } } },
      }
    );

    // Rapid updates — each one should cancel the previous timer
    rerender({ state: { cursor: { segment_index: 0, block_index: 1 } } });
    act(() => { vi.advanceTimersByTime(100); });

    rerender({ state: { cursor: { segment_index: 0, block_index: 2 } } });
    act(() => { vi.advanceTimersByTime(100); });

    rerender({ state: { cursor: { segment_index: 0, block_index: 3 } } });
    act(() => { vi.advanceTimersByTime(100); });

    // Still within debounce window — no call yet
    expect(spy).not.toHaveBeenCalled();

    // Allow the final timer to fire
    act(() => { vi.advanceTimersByTime(300); });

    // Only one PATCH call
    expect(spy).toHaveBeenCalledTimes(1);

    // And it sent the latest state (block_index: 3)
    const body = JSON.parse(
      (spy.mock.calls[0][1] as RequestInit).body as string
    );
    expect(body.cursor.block_index).toBe(3);

    vi.useRealTimers();
  });

  it("cancels pending PATCH on unmount (no fetch after unmount)", async () => {
    vi.useFakeTimers();
    const spy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue({ ok: true } as Response);

    const { rerender, unmount } = renderHook(
      ({ state }) => useAutosave({ sessionId: "s1", state }),
      {
        initialProps: { state: { cursor: { segment_index: 0, block_index: 0 } } },
      }
    );

    rerender({ state: { cursor: { segment_index: 1, block_index: 0 } } });

    // Unmount before the timer fires
    act(() => { vi.advanceTimersByTime(150); });
    unmount();

    // Advance past the debounce window — should not fire after unmount
    act(() => { vi.advanceTimersByTime(300); });

    expect(spy).not.toHaveBeenCalled();

    vi.useRealTimers();
  });
});
