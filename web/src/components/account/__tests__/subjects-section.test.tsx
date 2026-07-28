import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SubjectsSection } from "../subjects-section";

const PURE_MATHS_SUBJECT = {
  id: "pure_mathematics",
  subject: "pure_mathematics",
  exam_board: "edexcel",
  exam_level: "a_level",
  exam_date: null,
  target_grade: "A*",
  current_grade: null,
  readiness_pct: 62,
  session_count: 47,
  submission_count: 12,
};

describe("SubjectsSection", () => {
  it("removing subject shows named confirmation", async () => {
    const user = userEvent.setup();
    render(
      <SubjectsSection
        subjects={[PURE_MATHS_SUBJECT]}
      />
    );

    await user.click(screen.getByRole("button", { name: /Remove/ }));

    expect(
      await screen.findByText(
        /Removing Pure Mathematics will archive 47 sessions and 12 graded submissions/
      )
    ).toBeInTheDocument();
  });

  it("shows subject label in the row", () => {
    render(<SubjectsSection subjects={[PURE_MATHS_SUBJECT]} />);
    expect(screen.getByText("Pure Mathematics")).toBeInTheDocument();
  });

  it("shows empty state when no subjects", () => {
    render(<SubjectsSection subjects={[]} />);
    expect(screen.getByText(/No subjects added yet/)).toBeInTheDocument();
  });

  it("cancel closes the confirmation dialog", async () => {
    const user = userEvent.setup();
    render(<SubjectsSection subjects={[PURE_MATHS_SUBJECT]} />);

    await user.click(screen.getByRole("button", { name: /Remove/ }));
    await screen.findByText(
      /Removing Pure Mathematics will archive 47 sessions and 12 graded submissions/
    );

    await user.click(screen.getByRole("button", { name: /Cancel/ }));

    expect(
      screen.queryByText(
        /Removing Pure Mathematics will archive/
      )
    ).not.toBeInTheDocument();
  });
});
