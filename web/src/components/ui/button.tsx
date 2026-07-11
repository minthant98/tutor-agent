import { forwardRef } from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-[8px] font-sans text-[14px] font-medium transition-colors duration-[120ms] ease-[cubic-bezier(.22,.61,.36,1)] disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--primary)] text-white hover:bg-[var(--primary-focus)]",
        secondary:
          "bg-transparent border border-[var(--border-subtle)] text-[var(--text-primary)] hover:bg-[var(--surface-1)]",
        ghost:
          "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-1)]",
        destructive:
          "bg-transparent border border-[var(--semantic-danger-text)]/40 text-[var(--semantic-danger-text)] hover:bg-[var(--semantic-danger-bg)]",
      },
      size: {
        sm: "h-8 px-3",
        md: "h-10 px-4",
        lg: "h-12 px-6",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size }), className)}
        data-variant={variant ?? "primary"}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { buttonVariants };
