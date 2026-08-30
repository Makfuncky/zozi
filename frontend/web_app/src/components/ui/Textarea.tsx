"use client";
import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useFormGroup } from "./FormGroup";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, error, ...props }, ref) => {
  const formGroup = useFormGroup();
  const hasError = error || formGroup.error;

  return (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-lg border bg-surface-1 px-3 py-2 text-sm text-text placeholder:text-text-faint transition-colors resize-y min-h-[80px]",
        "focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand",
        hasError && "border-danger focus:ring-danger/30 focus:border-danger",
        className
      )}
      aria-invalid={hasError ? "true" : undefined}
      {...props}
    />
  );
});

Textarea.displayName = "Textarea";
