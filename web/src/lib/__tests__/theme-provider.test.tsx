import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ThemeProvider, useTheme } from "../theme-provider";

function Probe() {
  const { theme } = useTheme();
  return <div data-testid="theme">{theme ?? "unset"}</div>;
}

describe("ThemeProvider", () => {
  it("defaults to dark", async () => {
    render(<ThemeProvider><Probe /></ThemeProvider>);
    expect(await screen.findByTestId("theme")).toHaveTextContent("dark");
  });
});
