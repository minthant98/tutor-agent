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
    for (const stop of tokens.color.readiness) {
      expect(stop.toLowerCase()).not.toMatch(/^#([0-9a-f]{2})?[a-f0-9]f[a-f0-9]{3}$/);
    }
    expect(tokens.color.readiness).toHaveLength(5);
  });
  it("exports the shared ease token", () => {
    expect(tokens.motion.ease).toBe("cubic-bezier(.22, .61, .36, 1)");
  });
  it("motion durations are 120/220/320", () => {
    expect(tokens.motion.duration).toEqual({ fast: 120, base: 220, slow: 320 });
  });
});
