"use client";

import { ArrowUpRight, ArrowDownRight, Minus } from "@/lib/icons";

interface GrowthIndicatorProps {
  value: number;
  label?: string;
  size?: "sm" | "md";
  showLabel?: boolean;
}

export function GrowthIndicator({ value, label, size = "sm", showLabel = true }: GrowthIndicatorProps) {
  const isPositive = value > 0;
  const isNegative = value < 0;
  const isNeutral = value === 0;
  const sizeClass = size === "md" ? "text-sm" : "text-xs";

  let colorClass = "text-text-faint";
  let Icon = Minus;
  if (isPositive) {
    colorClass = "text-success";
    Icon = ArrowUpRight;
  } else if (isNegative) {
    colorClass = "text-danger";
    Icon = ArrowDownRight;
  }

  return (
    <span className={`${sizeClass} font-semibold flex items-center gap-0.5 ${colorClass}`}>
      <Icon className={size === "md" ? "w-4 h-4" : "w-3 h-3"} />
      {Math.abs(value).toFixed(1)}%
      {showLabel && label && <span className="text-text-faint font-normal ml-1">{label}</span>}
    </span>
  );
}
