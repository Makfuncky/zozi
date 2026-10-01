"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  indeterminate?: boolean;
  label?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({ className, indeterminate, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative flex items-center justify-center w-4 h-4 rounded border transition-colors", checked || indeterminate ? "bg-brand border-brand" : "border-border bg-surface-1")}>
        <input ref={ref} type="checkbox" className="sr-only" checked={checked} {...props} />
        {indeterminate ? "−" : checked ? "✓" : null}
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Checkbox.displayName = "Checkbox";
