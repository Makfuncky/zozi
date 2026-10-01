"use client";
import { cn } from "@/lib/utils";

type DividerOrientation = "horizontal" | "vertical";
type DividerVariant = "solid" | "dashed" | "dotted";

interface DividerProps {
  orientation?: DividerOrientation; variant?: DividerVariant; className?: string; label?: string;
}

const orientationClasses: Record<DividerOrientation, string> = {
  horizontal: "w-full border-t", vertical: "h-full border-l",
};
const variantClasses: Record<DividerVariant, string> = {
  solid: "border-solid", dashed: "border-dashed", dotted: "border-dotted",
};

export function Divider({ orientation = "horizontal", variant = "solid", className, label }: DividerProps) {
  if (label) {
    return (
      <div className={cn("flex items-center w-full", className)}>
        <div className={cn("flex-1 border-t border-glass-border-mid", variantClasses[variant])} />
        <span className="px-3 text-xs text-text-muted">{label}</span>
        <div className={cn("flex-1 border-t border-glass-border-mid", variantClasses[variant])} />
      </div>
    );
  }
  return <div className={cn("border-glass-border-mid", orientationClasses[orientation], variantClasses[variant], className)} role="separator" />;
}
