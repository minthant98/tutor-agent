import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Button } from "../button";

describe("Button", () => {
  it("renders each variant", () => {
    const { rerender } = render(<Button variant="primary">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("data-variant", "primary");
    rerender(<Button variant="secondary">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("data-variant", "secondary");
    rerender(<Button variant="ghost">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("data-variant", "ghost");
    rerender(<Button variant="destructive">Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("data-variant", "destructive");
  });
  it("fires onClick", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    await user.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });
  it("disables interaction when disabled", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Go
      </Button>
    );
    await user.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});
