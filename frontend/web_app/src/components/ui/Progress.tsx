"use client";
import { cn } from "@/lib/utils";

type ProgressVariant = "default" | "success" | "warning" | "danger";

interface ProgressProps {
  value: number;
  max?: number;
  variant?: ProgressVariant;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

const variantColors: Record<ProgressVariant, string> = {
  default: "bg-brand",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

const sizeClasses = { sm: "h-1", md: "h-2", lg: "h-3" };

export function Progress({ value, max = 100, variant = "default", size = "md", showLabel = false, className }: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-text-muted">Progress</span>
          <span className="text-xs font-medium text-text">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className={cn("w-full rounded-full bg-surface-2 overflow-hidden", sizeClasses[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-300", variantColors[variant])}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}
