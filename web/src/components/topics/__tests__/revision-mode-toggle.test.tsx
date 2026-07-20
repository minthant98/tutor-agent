import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { RevisionModeToggle, REVISION_MODE_KEY } from "../revision-mode-toggle";
import { applyRevisionMode } from "@/app/(app)/topics/page";
import type { TopicV3 } from "../types";

// ── RevisionModeToggle component tests ───────────────────────────────────────

describe("RevisionModeToggle", () => {
  it("renders the toggle with 'Revision mode' label", () => {
    render(<RevisionModeToggle value={false} onChange={() => {}} />);
    expect(screen.getByText("Revision mode")).toBeInTheDocument();
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  it("switch reflects value=false (unchecked)", () => {
    render(<RevisionModeToggle value={false} onChange={() => {}} />);
    const sw = screen.getByRole("switch");
    expect(sw).toHaveAttribute("data-state", "unchecked");
  });

  it("switch reflects value=true (checked)", () => {
    render(<RevisionModeToggle value={true} onChange={() => {}} />);
    const sw = screen.getByRole("switch");
    expect(sw).toHaveAttribute("data-state", "checked");
  });

  it("calls onChange when toggled", () => {
    const onChange = vi.fn();
    render(<RevisionModeToggle value={false} onChange={onChange} />);
    fireEvent.click(screen.getByRole("switch"));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(true);
  });
});

// ── sessionStorage persistence ────────────────────────────────────────────────

describe("RevisionMode sessionStorage persistence", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it("readRevisionMode returns false when key absent", async () => {
    const { readRevisionMode } = await import("../revision-mode-toggle");
    expect(readRevisionMode()).toBe(false);
  });

  it("writeRevisionMode + readRevisionMode round-trip true", async () => {
    const { readRevisionMode, writeRevisionMode } = await import("../revision-mode-toggle");
    writeRevisionMode(true);
    expect(sessionStorage.getItem(REVISION_MODE_KEY)).toBe("true");
    expect(readRevisionMode()).toBe(true);
  });

  it("writeRevisionMode + readRevisionMode round-trip false", async () => {
    const { readRevisionMode, writeRevisionMode } = await import("../revision-mode-toggle");
    sessionStorage.setItem(REVISION_MODE_KEY, "true");
    writeRevisionMode(false);
    expect(sessionStorage.getItem(REVISION_MODE_KEY)).toBe("false");
    expect(readRevisionMode()).toBe(false);
  });
});

// ── applyRevisionMode filter + sort logic ────────────────────────────────────

const makeTopics = (): TopicV3[] => [
  { id: "a", label: "A", mastery: 0, last_practised: "Never", status: "Not started", prerequisite: null },
  { id: "b", label: "B", mastery: 30, last_practised: "2 days ago", status: "Needs review", prerequisite: null },
  { id: "c", label: "C", mastery: 50, last_practised: "today", status: "Practising", prerequisite: null },
  { id: "d", label: "D", mastery: 80, last_practised: "today", status: "Mastered", prerequisite: null },
];

describe("applyRevisionMode", () => {
  it("excludes 'Not started' topics", () => {
    const result = applyRevisionMode(makeTopics());
    expect(result.map((t) => t.id)).not.toContain("a");
  });

  it("includes 'Needs review', 'Practising', 'Mastered' topics", () => {
    const result = applyRevisionMode(makeTopics());
    const ids = result.map((t) => t.id);
    expect(ids).toContain("b");
    expect(ids).toContain("c");
    expect(ids).toContain("d");
  });

  it("sorts by mastery ascending (lowest mastery first)", () => {
    const result = applyRevisionMode(makeTopics());
    const masteries = result.map((t) => t.mastery);
    for (let i = 1; i < masteries.length; i++) {
      expect(masteries[i]).toBeGreaterThanOrEqual(masteries[i - 1]);
    }
  });

  it("returns empty array when all topics are 'Not started'", () => {
    const allNotStarted: TopicV3[] = [
      { id: "x", label: "X", mastery: 0, last_practised: "Never", status: "Not started", prerequisite: null },
    ];
    expect(applyRevisionMode(allNotStarted)).toEqual([]);
  });

  it("does not mutate the original array", () => {
    const original = makeTopics();
    const copy = [...original];
    applyRevisionMode(original);
    expect(original).toEqual(copy);
  });
});
