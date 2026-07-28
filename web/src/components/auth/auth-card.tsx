"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { login, register, forgotPassword, getMe } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { identifyUser, track } from "@/lib/posthog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Logo from "@/components/Logo";

export type AuthMode = "signin" | "signup" | "reset";

interface AuthCardProps {
  mode: AuthMode;
}

/**
 * AuthCard — v3 400px centered Surface 1 card for auth pages.
 *
 * Three modes:
 *   - signin: email + password → POST /auth/login → redirect to /
 *   - signup: name + email + password → POST /auth/register → redirect to /onboarding/education-system
 *   - reset:  email only → POST /auth/forgot-password → redirect to /signin
 *
 * Design:
 *   - 400px max-width, Surface 1 bg, hairline border, rounded-card
 *   - Stride wordmark 20px above card
 *   - 44px height inputs (h-11), rounded-input, border-border-subtle
 *   - Password with Ghost eye-toggle (Lucide Eye/EyeOff)
 *   - Errors inline BELOW the field in muted-danger token — NEVER red borders, NEVER toasts
 *   - Title: exactly "Sign in", "Create account", "Reset password"
 *   - No ! marks. No emoji. No "Welcome back!"
 */
export function AuthCard({ mode }: AuthCardProps) {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Per-field errors
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [nameError, setNameError] = useState("");
  const [generalError, setGeneralError] = useState("");

  const clearErrors = useCallback(() => {
    setEmailError("");
    setPasswordError("");
    setNameError("");
    setGeneralError("");
  }, []);

  const handleSignIn = async () => {
    clearErrors();
    setLoading(true);
    try {
      const { access_token } = await login(email, password);
      setToken(access_token);
      const student = await getMe();
      identifyUser(student.id, {
        email: student.email,
        subscription_tier: student.subscription_tier,
        exam_board: student.exam_board,
      });
      track("login_completed");
      router.push("/");
    } catch {
      setPasswordError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    clearErrors();
    if (name.trim().length === 0) {
      setNameError("Name is required.");
      return;
    }
    if (password.length < 8) {
      setPasswordError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(email, name.trim(), password);
      const { access_token } = await login(email, password);
      setToken(access_token);
      try {
        const student = await getMe();
        identifyUser(student.id, {
          email: student.email,
          subscription_tier: student.subscription_tier,
        });
      } catch {
        // not fatal
      }
      track("signup_completed");
      router.push("/onboarding/education-system");
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status;
      if (status === 400) {
        setEmailError("An account with this email already exists.");
      } else {
        setGeneralError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    clearErrors();
    setLoading(true);
    try {
      await forgotPassword(email);
    } catch {
      // Swallow — always show confirmation to avoid email enumeration.
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "signin") handleSignIn();
    else if (mode === "signup") handleSignUp();
    else handleReset();
  };

  // ── Title map ─────────────────────────────────────────────────────────────
  const titles: Record<AuthMode, string> = {
    signin: "Sign in",
    signup: "Create account",
    reset: "Reset password",
  };

  // ── Reset submitted state ─────────────────────────────────────────────────
  if (mode === "reset" && submitted) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-[var(--surface-0)]">
        <div className="mb-5">
          <Logo size="md" href="/" />
        </div>
        <div className="w-full max-w-[400px] rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-8">
          <h1 className="mb-2 text-[20px] font-semibold text-[var(--text-primary)]">
            Check your inbox
          </h1>
          <p className="text-[14px] text-[var(--text-secondary)]">
            If an account exists for{" "}
            <span className="font-medium text-[var(--text-primary)]">{email}</span>,
            we sent a password reset link. The link expires in 1 hour.
          </p>
          <div className="mt-6">
            <Link
              href="/signin"
              className="text-[14px] text-[var(--primary)] hover:underline"
            >
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-[var(--surface-0)]">
      {/* Stride wordmark 20px above card */}
      <div className="mb-5">
        <Logo size="md" href="/" />
      </div>

      <div className="w-full max-w-[400px] rounded-card border border-[var(--border-subtle)] bg-[var(--surface-1)] p-8">
        <h1 className="mb-6 text-[20px] font-semibold text-[var(--text-primary)]">
          {titles[mode]}
        </h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
          {/* Name — signup only */}
          {mode === "signup" && (
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="auth-name"
                className="text-[13px] font-medium text-[var(--text-secondary)]"
              >
                Name
              </label>
              <Input
                id="auth-name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required
              />
              {nameError && (
                <p className="text-[13px] text-[var(--semantic-danger-text)]">
                  {nameError}
                </p>
              )}
            </div>
          )}

          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="auth-email"
              className="text-[13px] font-medium text-[var(--text-secondary)]"
            >
              Email
            </label>
            <Input
              id="auth-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
            {emailError && (
              <p className="text-[13px] text-[var(--semantic-danger-text)]">
                {emailError}
              </p>
            )}
          </div>

          {/* Password — signin + signup only */}
          {mode !== "reset" && (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="auth-password"
                  className="text-[13px] font-medium text-[var(--text-secondary)]"
                >
                  Password
                </label>
                {mode === "signin" && (
                  <Link
                    href="/reset"
                    className="text-[13px] text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                  >
                    Forgot password?
                  </Link>
                )}
              </div>
              <div className="relative">
                <Input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete={
                    mode === "signup" ? "new-password" : "current-password"
                  }
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "signup" ? "At least 8 characters" : "••••••••"}
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                >
                  {showPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
              {passwordError && (
                <p className="text-[13px] text-[var(--semantic-danger-text)]">
                  {passwordError}
                </p>
              )}
            </div>
          )}

          {/* General error */}
          {generalError && (
            <p className="text-[13px] text-[var(--semantic-danger-text)]">
              {generalError}
            </p>
          )}

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            size="md"
            className="w-full"
            disabled={loading}
          >
            {loading
              ? mode === "signin"
                ? "Signing in..."
                : mode === "signup"
                  ? "Creating account..."
                  : "Sending..."
              : mode === "signin"
                ? "Sign in"
                : mode === "signup"
                  ? "Create account"
                  : "Send reset link"}
          </Button>
        </form>

        {/* Footer links */}
        <div className="mt-6 text-center text-[13px] text-[var(--text-muted)]">
          {mode === "signin" && (
            <span>
              No account?{" "}
              <Link
                href="/signup"
                className="text-[var(--primary)] hover:underline"
              >
                Sign up
              </Link>
            </span>
          )}
          {mode === "signup" && (
            <span>
              Already have an account?{" "}
              <Link
                href="/signin"
                className="text-[var(--primary)] hover:underline"
              >
                Sign in
              </Link>
            </span>
          )}
          {mode === "reset" && (
            <Link
              href="/signin"
              className="text-[var(--primary)] hover:underline"
            >
              Back to sign in
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
