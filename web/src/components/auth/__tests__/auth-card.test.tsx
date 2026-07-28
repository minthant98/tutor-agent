import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AuthCard } from "../auth-card";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// Mock API calls — tests don't exercise submission
vi.mock("@/lib/api", () => ({
  login: vi.fn(),
  register: vi.fn(),
  forgotPassword: vi.fn(),
  getMe: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  setToken: vi.fn(),
  getToken: vi.fn(() => null),
}));

vi.mock("@/lib/posthog", () => ({
  identifyUser: vi.fn(),
  track: vi.fn(),
}));

vi.mock("@/components/Logo", () => ({
  default: () => <div data-testid="logo">Stride</div>,
}));

describe("AuthCard — signin mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sign-in title is exactly 'Sign in'", () => {
    render(<AuthCard mode="signin" />);
    expect(
      screen.getByRole("heading", { name: "Sign in" })
    ).toBeInTheDocument();
  });

  it("does not contain 'Welcome back' in any form", () => {
    render(<AuthCard mode="signin" />);
    expect(document.body.textContent).not.toMatch(/welcome back/i);
  });

  it("does not contain exclamation marks", () => {
    render(<AuthCard mode="signin" />);
    expect(document.body.textContent).not.toContain("!");
  });

  it("does not contain emoji", () => {
    render(<AuthCard mode="signin" />);
    const text = document.body.textContent!;
    expect(text).not.toContain("🎉");
    expect(text).not.toContain("👋");
  });

  it("renders email and password fields", () => {
    render(<AuthCard mode="signin" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    // Use the input element's label directly (not aria-label on the toggle button)
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("renders a password show/hide toggle button", () => {
    render(<AuthCard mode="signin" />);
    expect(
      screen.getByRole("button", { name: /show password/i })
    ).toBeInTheDocument();
  });

  it("does not render a Name field", () => {
    render(<AuthCard mode="signin" />);
    expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
  });
});

describe("AuthCard — signup mode", () => {
  it("renders 'Create account' as heading", () => {
    render(<AuthCard mode="signup" />);
    expect(
      screen.getByRole("heading", { name: "Create account" })
    ).toBeInTheDocument();
  });

  it("renders a Name field", () => {
    render(<AuthCard mode="signup" />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
  });

  it("does not contain exclamation marks", () => {
    render(<AuthCard mode="signup" />);
    expect(document.body.textContent).not.toContain("!");
  });
});

describe("AuthCard — reset mode", () => {
  it("renders 'Reset password' as heading", () => {
    render(<AuthCard mode="reset" />);
    expect(
      screen.getByRole("heading", { name: "Reset password" })
    ).toBeInTheDocument();
  });

  it("does not render a password field", () => {
    render(<AuthCard mode="reset" />);
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
  });

  it("does not contain banned praise words", () => {
    render(<AuthCard mode="reset" />);
    const text = document.body.textContent!.toLowerCase();
    for (const b of ["welcome", "amazing", "congratulations", "yay"]) {
      expect(text).not.toContain(b);
    }
  });
});
