import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Math } from "../math";

describe("Math", () => {
  it("renders KaTeX HTML for a block expression", () => {
    const { container } = render(<Math tex="x^2 + y^2 = z^2" />);
    // KaTeX outputs elements with katex- classnames
    const katexEl = container.querySelector(".katex");
    expect(katexEl).not.toBeNull();
  });

  it("renders KaTeX HTML for an inline expression", () => {
    const { container } = render(<Math tex="\frac{a}{b}" inline />);
    const katexEl = container.querySelector(".katex");
    expect(katexEl).not.toBeNull();
  });

  it("wraps output in a span with data-testid='math'", () => {
    render(<Math tex="E = mc^2" />);
    expect(screen.getByTestId("math")).toBeInTheDocument();
  });
});
