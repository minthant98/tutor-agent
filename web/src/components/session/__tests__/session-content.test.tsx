import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { SessionContent } from "../session-content";

// Mock katex CSS import inside math component — jsdom doesn't need it
vi.mock("katex/dist/katex.min.css", () => ({}));

// Mock react-katex to avoid full KaTeX render in unit tests
vi.mock("react-katex", () => ({
  InlineMath: ({ math }: { math: string }) => (
    <span className="katex" data-testid="inline-math">
      {math}
    </span>
  ),
  BlockMath: ({ math }: { math: string }) => (
    <div className="katex" data-testid="block-math">
      {math}
    </div>
  ),
}));

describe("SessionContent — TeachBlock", () => {
  it("renders teach block article with max-width 800px", () => {
    render(
      <SessionContent
        segment={{
          intent: "teach",
          blocks: [{ type: "prose", text: "Substitution is a technique..." }],
        }}
      />
    );
    const article = screen.getByRole("article");
    expect(article.className).toMatch(/max-w-\[800px\]/);
  });

  it("renders prose as a paragraph", () => {
    render(
      <SessionContent
        segment={{
          intent: "teach",
          blocks: [{ type: "prose", text: "Integration by parts" }],
        }}
      />
    );
    expect(screen.getByText("Integration by parts").tagName).toBe("P");
  });

  it("renders math block via Math component", () => {
    render(
      <SessionContent
        segment={{
          intent: "teach",
          blocks: [{ type: "math", tex: "x^2 + y^2" }],
        }}
      />
    );
    expect(screen.getByTestId("math")).toBeInTheDocument();
  });

  it("renders callout block with callout styling", () => {
    render(
      <SessionContent
        segment={{
          intent: "teach",
          blocks: [{ type: "callout", text: "Remember: always check signs" }],
        }}
      />
    );
    const callout = screen.getByText("Remember: always check signs");
    expect(callout.className).toMatch(/bg-/);
  });
});

describe("SessionContent — AssessBlock", () => {
  it("renders assess block with max-width 880px", () => {
    render(
      <SessionContent
        segment={{
          intent: "assess",
          question: { text: "Integrate x^2 dx", max_marks: 4 },
        }}
      />
    );
    // The outer wrapper should have max-w-[880px]
    const wrapper = screen.getByRole("region", { name: /question/i });
    expect(wrapper.className).toMatch(/max-w-\[880px\]/);
  });

  it("renders marks chip with correct value", () => {
    render(
      <SessionContent
        segment={{
          intent: "assess",
          question: { text: "Integrate x^2 dx", max_marks: 4 },
        }}
      />
    );
    expect(screen.getByText("[4 marks]")).toBeInTheDocument();
  });

  it("renders question text", () => {
    render(
      <SessionContent
        segment={{
          intent: "assess",
          question: { text: "Differentiate sin(x)", max_marks: 2 },
        }}
      />
    );
    expect(screen.getByText("Differentiate sin(x)")).toBeInTheDocument();
  });
});

describe("SessionContent — ReinforceBlock", () => {
  it("shows step 1 initially", () => {
    render(
      <SessionContent
        segment={{
          intent: "reinforce",
          steps: [
            { id: "s1", text: "step 1" },
            { id: "s2", text: "step 2" },
          ],
        }}
      />
    );
    expect(screen.getByText("step 1")).toBeInTheDocument();
  });

  it("hides step 2 initially", () => {
    render(
      <SessionContent
        segment={{
          intent: "reinforce",
          steps: [
            { id: "s1", text: "step 1" },
            { id: "s2", text: "step 2" },
          ],
        }}
      />
    );
    expect(screen.queryByText("step 2")).not.toBeInTheDocument();
  });

  it("reveals step 2 after pressing Space", async () => {
    const user = userEvent.setup();
    render(
      <SessionContent
        segment={{
          intent: "reinforce",
          steps: [
            { id: "s1", text: "step 1" },
            { id: "s2", text: "step 2" },
          ],
        }}
      />
    );
    expect(screen.queryByText("step 2")).not.toBeInTheDocument();
    await user.keyboard(" ");
    expect(screen.getByText("step 2")).toBeInTheDocument();
  });

  it("renders optional followUp as assess block after all steps revealed", async () => {
    const user = userEvent.setup();
    render(
      <SessionContent
        segment={{
          intent: "reinforce",
          steps: [{ id: "s1", text: "only step" }],
          followUp: { text: "Now try it yourself", max_marks: 3 },
        }}
      />
    );
    // advance past the only step
    await user.keyboard(" ");
    expect(screen.getByText("[3 marks]")).toBeInTheDocument();
  });
});
