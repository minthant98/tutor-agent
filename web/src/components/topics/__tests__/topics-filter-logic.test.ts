import { describe, it, expect } from "vitest";
import { isWithinDays, applyFilters } from "@/app/(app)/topics/page";
import type { TopicV3 } from "../types";

// ── isWithinDays ──────────────────────────────────────────────────────────────

describe("isWithinDays", () => {
  it("'today' is within any positive bound", () => {
    expect(isWithinDays("today", 1)).toBe(true);
    expect(isWithinDays("today", 7)).toBe(true);
    expect(isWithinDays("today", 30)).toBe(true);
  });

  it("'yesterday' is within any positive bound", () => {
    expect(isWithinDays("yesterday", 1)).toBe(true);
    expect(isWithinDays("yesterday", 7)).toBe(true);
  });

  it("'7 days ago' is within 7 days (boundary — inclusive)", () => {
    expect(isWithinDays("7 days ago", 7)).toBe(true);
  });

  it("'8 days ago' is NOT within 7 days", () => {
    expect(isWithinDays("8 days ago", 7)).toBe(false);
  });

  it("'20 days ago' is NOT within 7 days", () => {
    expect(isWithinDays("20 days ago", 7)).toBe(false);
  });

  it("'20 days ago' IS within 30 days", () => {
    expect(isWithinDays("20 days ago", 30)).toBe(true);
  });

  it("'30 days ago' is within 30 days (boundary — inclusive)", () => {
    expect(isWithinDays("30 days ago", 30)).toBe(true);
  });

  it("'31 days ago' is NOT within 30 days", () => {
    expect(isWithinDays("31 days ago", 30)).toBe(false);
  });

  it("'1 week ago' (7 days) is within 7 days", () => {
    expect(isWithinDays("1 week ago", 7)).toBe(true);
  });

  it("'2 weeks ago' (14 days) is NOT within 7 days but IS within 30 days", () => {
    expect(isWithinDays("2 weeks ago", 7)).toBe(false);
    expect(isWithinDays("2 weeks ago", 30)).toBe(true);
  });

  it("'last week' is within 7 days", () => {
    expect(isWithinDays("last week", 7)).toBe(true);
    expect(isWithinDays("last week", 30)).toBe(true);
  });

  it("'Never' returns false", () => {
    expect(isWithinDays("Never", 7)).toBe(false);
    expect(isWithinDays("Never", 30)).toBe(false);
  });
});

// ── applyFilters recency ──────────────────────────────────────────────────────

function makeTopic(last_practised: string): TopicV3 {
  return {
    id: "t1",
    label: "Test",
    mastery: 50,
    last_practised,
    status: "Practising",
    prerequisite: null,
  };
}

describe("applyFilters — recency", () => {
  it("within_7d excludes '20 days ago'", () => {
    const topics = [makeTopic("20 days ago"), makeTopic("3 days ago")];
    const result = applyFilters(topics, [], "within_7d");
    expect(result).toHaveLength(1);
    expect(result[0].last_practised).toBe("3 days ago");
  });

  it("within_7d includes '7 days ago' (boundary — inclusive)", () => {
    const topics = [makeTopic("7 days ago")];
    const result = applyFilters(topics, [], "within_7d");
    expect(result).toHaveLength(1);
  });

  it("within_7d excludes '8 days ago'", () => {
    const topics = [makeTopic("8 days ago")];
    const result = applyFilters(topics, [], "within_7d");
    expect(result).toHaveLength(0);
  });

  it("within_30d includes '20 days ago' but excludes 'Never'", () => {
    const topics = [makeTopic("20 days ago"), makeTopic("Never")];
    const result = applyFilters(topics, [], "within_30d");
    expect(result).toHaveLength(1);
    expect(result[0].last_practised).toBe("20 days ago");
  });

  it("never filter matches only 'Never'", () => {
    const topics = [makeTopic("Never"), makeTopic("today"), makeTopic("5 days ago")];
    const result = applyFilters(topics, [], "never");
    expect(result).toHaveLength(1);
    expect(result[0].last_practised).toBe("Never");
  });
});
