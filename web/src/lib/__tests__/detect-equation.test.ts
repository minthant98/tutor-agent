import { describe, it, expect } from "vitest";
import { hasEquationPattern } from "../detect-equation";

describe("hasEquationPattern", () => {
  it("returns true for superscript (x^2)", () => {
    expect(hasEquationPattern("x^2")).toBe(true);
  });

  it("returns true for LaTeX frac command (\\frac{a}{b})", () => {
    expect(hasEquationPattern("\\frac{a}{b}")).toBe(true);
  });

  it("returns true for subscript (y_1)", () => {
    expect(hasEquationPattern("y_1")).toBe(true);
  });

  it("returns true for backslash command (\\sqrt)", () => {
    expect(hasEquationPattern("\\sqrt{x}")).toBe(true);
  });

  it("returns false for plain text", () => {
    expect(hasEquationPattern("just plain text")).toBe(false);
  });

  it("returns false for numbers only", () => {
    expect(hasEquationPattern("42 is the answer")).toBe(false);
  });
});
