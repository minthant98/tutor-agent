import { describe, it, expect } from "vitest";
import { tokens } from "../design-tokens";

describe("design tokens", () => {
  it("exports the primary indigo", () => {
    expect(tokens.color.primary).toBe("#6268F2");
  });
  it("exports the type scale in ascending order", () => {
    expect(tokens.type.scale).toEqual([11, 12, 14, 16, 20, 24, 32, 40]);
  });
  it("readiness gradient contains no green stop", () => {
    expect(tokens.color.readiness).toHaveLength(5);
    for (const stop of tokens.color.readiness) {
      // Parse hex #RRGGBB
      const rgb = stop.replace("#", "");
      const r = parseInt(rgb.slice(0, 2), 16);
      const g = parseInt(rgb.slice(2, 4), 16);
      const b = parseInt(rgb.slice(4, 6), 16);
      // A "green" pixel: G is the dominant channel by a meaningful margin
      const isGreenDominant = g > r + 20 && g > b + 20;
      expect(isGreenDominant, `stop ${stop} looks green`).toBe(false);
    }
  });
  it("exports the shared ease token", () => {
    expect(tokens.motion.ease).toBe("cubic-bezier(.22, .61, .36, 1)");
  });
  it("motion durations are 120/220/320", () => {
    expect(tokens.motion.duration).toEqual({ fast: 120, base: 220, slow: 320 });
  });
});
