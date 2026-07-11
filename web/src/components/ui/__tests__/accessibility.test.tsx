import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, it, expect } from "vitest";
import { Button } from "../button";
import { Input } from "../input";
import { Card } from "../card";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "../dialog";

expect.extend(toHaveNoViolations);

describe("primitives are accessible", () => {
  it("Button", async () => {
    const { container } = render(<Button>Go</Button>);
    expect(await axe(container)).toHaveNoViolations();
  });
  it("Input has associated label", async () => {
    const { container } = render(
      <label>
        Email
        <Input id="email" name="email" />
      </label>
    );
    expect(await axe(container)).toHaveNoViolations();
  });
  it("Card", async () => {
    const { container } = render(
      <Card>
        <h2>Title</h2>
        <p>Body</p>
      </Card>
    );
    expect(await axe(container)).toHaveNoViolations();
  });
  it("Dialog", async () => {
    const { container } = render(
      <Dialog open>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Confirm</DialogTitle>
        </DialogContent>
      </Dialog>
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
