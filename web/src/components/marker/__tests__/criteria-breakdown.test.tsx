import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CriteriaBreakdown } from "../criteria-breakdown";
import type { GradingCriterion } from "@/lib/types";

const AWARDED_CRITERION: GradingCriterion = {
  code: "M1",
  description: "Chain rule applied correctly",
  awarded: true,
  comment: "",
};

const NOT_AWARDED_CRITERION: GradingCriterion = {
  code: "A1",
  description: "Correct value obtained",
  awarded: false,
  comment: "Sign error in final step",
};

describe("CriteriaBreakdown — a11y: status is never color-only", () => {
  it("awarded row has both check icon (aria-label) and 'Awarded' text label", () => {
    render(<CriteriaBreakdown criteria={[AWARDED_CRITERION]} />);
    // getByRole("row") excludes header — but with role="table" pattern there is one data row
    // We use the criteria code to find the row via its aria-label
    const row = screen.getByRole("row", { name: /Awarded: Chain rule applied correctly/i });
    expect(within(row).getByLabelText("Awarded")).toBeInTheDocument(); // icon
    expect(within(row).getByText("Awarded")).toBeInTheDocument();        // text label
  });

  it("not-awarded row has dash glyph and 'Not awarded' text (never red X)", () => {
    render(<CriteriaBreakdown criteria={[NOT_AWARDED_CRITERION]} />);
    const row = screen.getByRole("row", { name: /Not awarded: Correct value obtained/i });
    expect(within(row).getByText("—")).toBeInTheDocument();              // glyph
    expect(within(row).getByText("Not awarded")).toBeInTheDocument();    // text label
    // Regression: no red X / incorrect icon
    expect(within(row).queryByLabelText(/incorrect|error|wrong/i)).not.toBeInTheDocument();
  });

  it("renders multiple rows — one per criterion", () => {
    render(
      <CriteriaBreakdown criteria={[AWARDED_CRITERION, NOT_AWARDED_CRITERION]} />
    );
    // Two data rows (not counting header which also has role=row)
    const rows = screen.getAllByRole("row");
    // 1 header + 2 data rows
    expect(rows.length).toBe(3);
  });

  it("renders criterion code in the row", () => {
    render(<CriteriaBreakdown criteria={[AWARDED_CRITERION]} />);
    expect(screen.getByText("M1")).toBeInTheDocument();
  });

  it("renders criterion description in the row", () => {
    render(<CriteriaBreakdown criteria={[NOT_AWARDED_CRITERION]} />);
    expect(screen.getByText("Correct value obtained")).toBeInTheDocument();
  });

  it("renders the comment when present", () => {
    render(<CriteriaBreakdown criteria={[NOT_AWARDED_CRITERION]} />);
    expect(screen.getByText("Sign error in final step")).toBeInTheDocument();
  });

  it("renders empty criteria list without errors", () => {
    render(<CriteriaBreakdown criteria={[]} />);
    // Table still renders with header
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("row aria-label uses 'Awarded' prefix for awarded criteria", () => {
    render(<CriteriaBreakdown criteria={[AWARDED_CRITERION]} />);
    expect(
      screen.getByRole("row", { name: /^Awarded: Chain rule applied correctly$/i })
    ).toBeInTheDocument();
  });

  it("row aria-label uses 'Not awarded' prefix for not-awarded criteria", () => {
    render(<CriteriaBreakdown criteria={[NOT_AWARDED_CRITERION]} />);
    expect(
      screen.getByRole("row", { name: /^Not awarded: Correct value obtained$/i })
    ).toBeInTheDocument();
  });
});
