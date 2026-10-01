"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(({ className, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative flex items-center justify-center w-4 h-4 rounded-full border transition-colors", checked ? "border-brand" : "border-border bg-surface-1")}>
        <input ref={ref} type="radio" className="sr-only" checked={checked} {...props} />
        {checked && <span className="w-2 h-2 rounded-full bg-brand" />}
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Radio.displayName = "Radio";
