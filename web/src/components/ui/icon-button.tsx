import { forwardRef } from "react";
import { Button, type ButtonProps } from "./button";
import { cn } from "@/lib/utils";

export interface IconButtonProps extends Omit<ButtonProps, "size"> {
  size?: "icon";
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, size = "icon", ...props }, ref) => {
    return (
      <Button
        ref={ref}
        className={cn("h-10 w-10 p-0", className)}
        size="md"
        {...props}
      />
    );
  }
);
IconButton.displayName = "IconButton";
