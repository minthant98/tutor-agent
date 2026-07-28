import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PlannerTransparency } from "../planner-transparency";

const SEGMENTS = [
  { intent: "teach", topic: "Integration" },
  { intent: "reinforce", topic: "Substitution" },
  { intent: "assess", topic: "Partial Fractions" },
];

describe("PlannerTransparency", () => {
  it("shows plan segments, minutes and both actions", () => {
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="targeting substitution"
        onStart={vi.fn()}
        onChangeMode={vi.fn()}
      />
    );
    expect(screen.getByText(/Today's Plan/)).toBeInTheDocument();
    expect(screen.getByText(/≈18 minutes · 3 segments/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Change mode/ })).toBeInTheDocument();
  });

  it("renders all segment rows", () => {
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="test"
        onStart={vi.fn()}
        onChangeMode={vi.fn()}
      />
    );
    expect(screen.getByText("Integration")).toBeInTheDocument();
    expect(screen.getByText("Substitution")).toBeInTheDocument();
    expect(screen.getByText("Partial Fractions")).toBeInTheDocument();
    // Intent column text
    expect(screen.getByText("teach")).toBeInTheDocument();
    expect(screen.getByText("reinforce")).toBeInTheDocument();
    expect(screen.getByText("assess")).toBeInTheDocument();
  });

  it("renders Alex narration text", () => {
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="Coming from your Exam Marker result — targeting substitution."
        onStart={vi.fn()}
        onChangeMode={vi.fn()}
      />
    );
    expect(
      screen.getByText(/Coming from your Exam Marker result/)
    ).toBeInTheDocument();
  });

  it("calls onStart when Start button is clicked", () => {
    const onStart = vi.fn();
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="test"
        onStart={onStart}
        onChangeMode={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Start/ }));
    expect(onStart).toHaveBeenCalledOnce();
  });

  it("calls onChangeMode when Change mode button is clicked", () => {
    const onChangeMode = vi.fn();
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="test"
        onStart={vi.fn()}
        onChangeMode={onChangeMode}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Change mode/ }));
    expect(onChangeMode).toHaveBeenCalledOnce();
  });

  it("triggers onStart when Enter is pressed", () => {
    const onStart = vi.fn();
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="test"
        onStart={onStart}
        onChangeMode={vi.fn()}
      />
    );
    fireEvent.keyDown(document, { key: "Enter" });
    expect(onStart).toHaveBeenCalledOnce();
  });

  it("shows h1 heading 'Today's Plan'", () => {
    render(
      <PlannerTransparency
        segments={SEGMENTS}
        minutes={18}
        narration="test"
        onStart={vi.fn()}
        onChangeMode={vi.fn()}
      />
    );
    expect(
      screen.getByRole("heading", { name: /Today's Plan/ })
    ).toBeInTheDocument();
  });
});
