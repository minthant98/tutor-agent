import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-11 w-full rounded-[8px] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-3 py-2 text-[14px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors duration-[120ms] ease-[cubic-bezier(.22,.61,.36,1)] disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
