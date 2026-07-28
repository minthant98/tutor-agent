import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MarkSchemeAccordion } from "../mark-scheme-accordion";

const SAMPLE_SCHEME = "M1 [awarded]\nA1 [not-awarded target]\nB1";

describe("MarkSchemeAccordion", () => {
  let scrollSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    scrollSpy = vi.spyOn(HTMLElement.prototype, "scrollIntoView").mockImplementation(() => {});
  });

  afterEach(() => {
    act(() => { vi.runAllTimers(); });
    vi.useRealTimers();
    scrollSpy.mockRestore();
    vi.clearAllMocks();
  });

  it("renders closed by default — trigger button is present", () => {
    render(
      <MarkSchemeAccordion scheme={SAMPLE_SCHEME} firstNotAwardedRef="A1" />
    );
    expect(screen.getByRole("button", { name: /Mark scheme/i })).toBeInTheDocument();
  });

  it("shows scheme text after opening", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <MarkSchemeAccordion scheme={SAMPLE_SCHEME} firstNotAwardedRef={null} />
    );
    await user.click(screen.getByRole("button", { name: /Mark scheme/i }));
    act(() => { vi.runAllTimers(); });
    expect(screen.getByText(/M1 \[awarded\]/)).toBeInTheDocument();
  });

  it("auto-scrolls to first not-awarded criterion when opened with firstNotAwardedRef", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <MarkSchemeAccordion scheme={SAMPLE_SCHEME} firstNotAwardedRef="A1" />
    );
    await user.click(screen.getByRole("button", { name: /Mark scheme/i }));
    act(() => { vi.runAllTimers(); });
    expect(scrollSpy).toHaveBeenCalledWith(
      expect.objectContaining({ behavior: "smooth" })
    );
  });

  it("does NOT auto-scroll when firstNotAwardedRef is null", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <MarkSchemeAccordion scheme={SAMPLE_SCHEME} firstNotAwardedRef={null} />
    );
    await user.click(screen.getByRole("button", { name: /Mark scheme/i }));
    act(() => { vi.runAllTimers(); });
    expect(scrollSpy).not.toHaveBeenCalled();
  });

  it("falls back to scrolling the pre element when code is not found in scheme text", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <MarkSchemeAccordion scheme="M1 only this criterion" firstNotAwardedRef="Z9" />
    );
    await user.click(screen.getByRole("button", { name: /Mark scheme/i }));
    act(() => { vi.runAllTimers(); });
    expect(scrollSpy).toHaveBeenCalledWith(
      expect.objectContaining({ behavior: "smooth" })
    );
  });

  it("renders scheme content in a pre element with whitespace-pre-wrap and font-mono classes", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) });
    render(
      <MarkSchemeAccordion scheme={SAMPLE_SCHEME} firstNotAwardedRef={null} />
    );
    await user.click(screen.getByRole("button", { name: /Mark scheme/i }));
    act(() => { vi.runAllTimers(); });
    const pre = screen.getByText(/M1 \[awarded\]/).closest("pre");
    expect(pre).toBeInTheDocument();
    expect(pre?.className).toContain("font-mono");
    expect(pre?.className).toContain("whitespace-pre-wrap");
  });
});
