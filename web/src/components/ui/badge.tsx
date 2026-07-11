import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[12px] font-medium transition-colors duration-[120ms] ease-[cubic-bezier(.22,.61,.36,1)]",
  {
    variants: {
      variant: {
        default: "bg-[var(--primary)] text-white",
        secondary: "bg-[var(--surface-1)] text-[var(--text-secondary)] border border-[var(--border-subtle)]",
        success: "bg-[var(--semantic-success-bg)] text-[var(--semantic-success-text)]",
        warning: "bg-[var(--semantic-warning-bg)] text-[var(--semantic-warning-text)]",
        destructive: "bg-[var(--semantic-danger-bg)] text-[var(--semantic-danger-text)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
