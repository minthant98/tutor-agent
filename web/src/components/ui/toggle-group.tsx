"use client";

import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cn } from "@/lib/utils";

const ToggleGroupContext = React.createContext<{
  size?: "sm" | "md" | "lg";
  variant?: "default" | "outline";
}>({});

export const ToggleGroup = React.forwardRef<
  React.ComponentRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root> & {
    variant?: "default" | "outline";
    size?: "sm" | "md" | "lg";
  }
>(({ className, variant = "default", size = "md", children, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    className={cn("flex items-center justify-center gap-1", className)}
    {...props}
  >
    <ToggleGroupContext.Provider value={{ variant, size }}>
      {children}
    </ToggleGroupContext.Provider>
  </ToggleGroupPrimitive.Root>
));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

export const ToggleGroupItem = React.forwardRef<
  React.ComponentRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> & {
    variant?: "default" | "outline";
    size?: "sm" | "md" | "lg";
  }
>(({ className, children, variant, size, ...props }, ref) => {
  const context = React.useContext(ToggleGroupContext);
  const resolvedVariant = variant ?? context.variant ?? "default";
  const resolvedSize = size ?? context.size ?? "md";

  return (
    <ToggleGroupPrimitive.Item
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-input font-medium text-[14px] transition-all duration-fast ease-standard disabled:pointer-events-none disabled:opacity-50",
        resolvedSize === "sm" && "h-8 px-2.5",
        resolvedSize === "md" && "h-10 px-3",
        resolvedSize === "lg" && "h-12 px-4",
        resolvedVariant === "default" &&
          "bg-transparent text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] data-[state=on]:bg-[var(--surface-2)] data-[state=on]:text-[var(--text-primary)]",
        resolvedVariant === "outline" &&
          "border border-[var(--border-subtle)] bg-transparent text-[var(--text-secondary)] hover:bg-[var(--surface-1)] data-[state=on]:bg-[var(--surface-1)] data-[state=on]:text-[var(--text-primary)]",
        className
      )}
      {...props}
    >
      {children}
    </ToggleGroupPrimitive.Item>
  );
});
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;
