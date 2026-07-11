import { forwardRef } from "react";
import { cn } from "@/lib/utils";

type Surface = "0" | "1" | "2" | "3";

const surfaceClasses: Record<Surface, string> = {
  "0": "bg-[var(--surface-0)]",
  "1": "bg-[var(--surface-1)]",
  "2": "bg-[var(--surface-2)]",
  "3": "bg-[var(--surface-3)]",
};

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  "data-surface"?: Surface;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, "data-surface": surface = "2", ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-surface={surface}
        className={cn(
          "rounded-card border border-[var(--border-subtle)] p-4",
          surfaceClasses[surface],
          className
        )}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-1.5 p-4", className)} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("text-[16px] font-semibold text-[var(--text-primary)]", className)} {...props} />
  )
);
CardTitle.displayName = "CardTitle";

export const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-4 pt-0", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center p-4 pt-0", className)} {...props} />
  )
);
CardFooter.displayName = "CardFooter";
