"use client";
import { cn } from "@/lib/utils";
type StatusKey = "success" | "danger" | "warning" | "info";
const dotColors: Record<StatusKey, string> = { success: "bg-success", danger: "bg-danger", warning: "bg-warning", info: "bg-info" };
interface StatusBadgeProps { status: StatusKey; label: string; className?: string; }
export function StatusBadge({ status: statusKey, label, className }: StatusBadgeProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border border-glass-border-mid bg-glass-base", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", dotColors[statusKey])} />
      {label}
    </span>
  );
}
