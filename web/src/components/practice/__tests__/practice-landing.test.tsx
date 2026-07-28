import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { PracticeLanding } from "../practice-landing";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const DATA = {
  narration:
    "Integration Basics and Partial Fractions account for most recent lost marks. Today's practice can address either.",
  weak_topics: [
    { id: "integration_basics", label: "Integration Basics" },
    { id: "partial_fractions", label: "Partial Fractions" },
  ],
};

describe("PracticeLanding", () => {
  it("shows the header question", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    expect(
      screen.getByRole("heading", {
        name: /How do you want to practice today\?/,
      })
    ).toBeInTheDocument();
  });

  it("renders Alex narration text", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    expect(screen.getByText(/Integration Basics and Partial Fractions/)).toBeInTheDocument();
  });

  it("renders exactly three mode cards", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    expect(screen.getAllByTestId(/^mode-card-/)).toHaveLength(3);
    expect(screen.getByTestId("mode-card-quick-practice")).toBeInTheDocument();
    expect(screen.getByTestId("mode-card-weak-areas")).toBeInTheDocument();
    expect(screen.getByTestId("mode-card-drill-in")).toBeInTheDocument();
  });

  it("Quick Practice card has exactly one Start CTA", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    const card = screen.getByTestId("mode-card-quick-practice");
    const buttons = within(card).getAllByRole("button");
    expect(buttons).toHaveLength(1);
    expect(within(card).getByRole("button")).toHaveTextContent(/^Start$/);
  });

  it("Weak Areas card shows topic chips from weak_topics", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    const card = screen.getByTestId("mode-card-weak-areas");
    expect(within(card).getByText("Integration Basics")).toBeInTheDocument();
    expect(within(card).getByText("Partial Fractions")).toBeInTheDocument();
  });

  it("Weak Areas card has exactly one Start CTA", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    const card = screen.getByTestId("mode-card-weak-areas");
    // Only one primary button named Start
    const startBtns = within(card).getAllByRole("button", { name: /^Start$/ });
    expect(startBtns).toHaveLength(1);
  });

  it("Drill-In Start disabled until topic chosen", async () => {
    const user = userEvent.setup();
    render(
      <PracticeLanding
        data={DATA}
        topics={[{ id: "integration_basics", label: "Integration Basics" }]}
      />
    );
    const card = screen.getByTestId("mode-card-drill-in");

    // Start is disabled initially
    expect(within(card).getByRole("button", { name: "Start" })).toBeDisabled();

    // Open the combobox
    await user.click(within(card).getByRole("combobox"));

    // Select an option
    const option = await screen.findByRole("option", {
      name: /Integration Basics/,
    });
    await user.click(option);

    // Start is now enabled
    expect(within(card).getByRole("button", { name: "Start" })).toBeEnabled();
  });

  it("Drill-In Start remains disabled when no topics passed", () => {
    render(<PracticeLanding data={DATA} topics={[]} />);
    const card = screen.getByTestId("mode-card-drill-in");
    expect(within(card).getByRole("button", { name: "Start" })).toBeDisabled();
  });

  it("Drill-In shows 'Choose a topic' meta label when no topic selected", () => {
    render(
      <PracticeLanding
        data={DATA}
        topics={[{ id: "integration_basics", label: "Integration Basics" }]}
      />
    );
    const card = screen.getByTestId("mode-card-drill-in");
    expect(within(card).getByText("Choose a topic")).toBeInTheDocument();
  });

  it("Drill-In shows '~12 min · targeted' meta label after topic chosen", async () => {
    const user = userEvent.setup();
    render(
      <PracticeLanding
        data={DATA}
        topics={[{ id: "integration_basics", label: "Integration Basics" }]}
      />
    );
    const card = screen.getByTestId("mode-card-drill-in");

    // Open combobox and select a topic
    await user.click(within(card).getByRole("combobox"));
    const option = await screen.findByRole("option", {
      name: /Integration Basics/,
    });
    await user.click(option);

    expect(within(card).getByText("~12 min · targeted")).toBeInTheDocument();
  });
});
