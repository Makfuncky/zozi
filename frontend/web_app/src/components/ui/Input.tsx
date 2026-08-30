"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useFormGroup } from "./FormGroup";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-lg border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
        hasError && "border-danger focus:ring-danger/30 focus:border-danger",
        className
      )}
      aria-invalid={hasError ? "true" : undefined}
      {...props}
    />
  );
});

Input.displayName = "Input";
