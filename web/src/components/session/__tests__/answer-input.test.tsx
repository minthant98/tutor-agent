import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AnswerInput } from "../answer-input";

describe("AnswerInput", () => {
  it("shows hint when empty", () => {
    render(<AnswerInput onSubmit={vi.fn()} />);
    expect(
      screen.getByText(/Show working\. Alex marks method as well as answer\./)
    ).toBeInTheDocument();
  });

  it("hint disappears when user types", async () => {
    const user = userEvent.setup();
    render(<AnswerInput onSubmit={vi.fn()} />);
    const ta = screen.getByRole("textbox");
    await user.type(ta, "hello");
    expect(
      screen.queryByText(/Show working\. Alex marks method as well as answer\./)
    ).not.toBeInTheDocument();
  });

  it("switches to mono font when equation pattern typed", async () => {
    const user = userEvent.setup();
    render(<AnswerInput onSubmit={vi.fn()} />);
    const ta = screen.getByRole("textbox");
    await user.type(ta, "x^2 + 3");
    expect(ta).toHaveClass("font-mono");
  });

  it("does not switch to mono for plain text", async () => {
    const user = userEvent.setup();
    render(<AnswerInput onSubmit={vi.fn()} />);
    const ta = screen.getByRole("textbox");
    await user.type(ta, "just plain text");
    expect(ta).not.toHaveClass("font-mono");
  });

  it("submits on Cmd+Enter", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AnswerInput onSubmit={onSubmit} />);
    await user.type(screen.getByRole("textbox"), "answer");
    await user.keyboard("{Meta>}{Enter}{/Meta}");
    expect(onSubmit).toHaveBeenCalledWith("answer");
  });

  it("does not submit on plain Enter (inserts newline)", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AnswerInput onSubmit={onSubmit} />);
    await user.type(screen.getByRole("textbox"), "answer");
    await user.keyboard("{Enter}");
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
