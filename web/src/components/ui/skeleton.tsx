import { cn } from "@/lib/utils";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-input bg-[var(--surface-1)]",
        className
      )}
      {...props}
    />
  );
}
