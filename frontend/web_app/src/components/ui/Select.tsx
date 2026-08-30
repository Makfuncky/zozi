"use client";
import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useFormGroup } from "./FormGroup";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({ className, children, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          "w-full appearance-none rounded-lg border bg-surface-1 px-3 py-2 pr-8 text-sm text-text transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
          hasError && "border-danger focus:ring-danger/30 focus:border-danger",
          className
        )}
        aria-invalid={hasError ? "true" : undefined}
        {...props}
      >
        {children}
      </select>
      <span className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none">▾</span>
    </div>
  );
});

Select.displayName = "Select";
