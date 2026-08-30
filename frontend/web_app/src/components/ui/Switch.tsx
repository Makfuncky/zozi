"use client";
import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(({ className, label, checked, ...props }, ref) => {
  return (
    <label className={cn("inline-flex items-center gap-2 cursor-pointer text-sm text-text", className)}>
      <span className={cn("relative w-9 h-5 rounded-full transition-colors", checked ? "bg-brand" : "bg-surface-2")}>
        <input ref={ref} type="checkbox" role="switch" className="sr-only" checked={checked} {...props} />
        <span className={cn("absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform", checked && "translate-x-4")} />
      </span>
      {label && <span>{label}</span>}
    </label>
  );
});

Switch.displayName = "Switch";
