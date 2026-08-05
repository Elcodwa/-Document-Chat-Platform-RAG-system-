import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-ink placeholder:text-ink-faint",
          "transition-colors focus:border-accent focus:outline-none",
          "disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-ink-faint",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
