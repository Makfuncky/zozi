"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant = 
  | "success" 
  | "warning" 
  | "danger" 
  | "info" 
  | "default"
  | "outline";

export interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export function Badge({ variant = "default", className, children, icon }: BadgeProps) {
  const variantClasses = {
    success: "bg-success/15 text-success border-success/30 shadow-success/20",
    warning: "bg-warning/15 text-warning border-warning/30 shadow-warning/20",
    danger: "bg-danger/15 text-danger border-danger/30 shadow-danger/20",
    info: "bg-info/15 text-info border-info/30 shadow-info/20",
    default: "bg-glass-mid text-text-muted border-glass-border-mid",
    outline: "bg-transparent border border-glass-border-mid text-text-muted",
  };

  return (
    <span className={cn(
      "text-[10px] px-2 py-0.5 rounded inline-flex items-center gap-1 font-medium border backdrop-blur",
      variantClasses[variant],
      className
    )}>
      {icon && icon}
      {children}
    </span>
  );
}

/**
 * Status badge with predefined status-to-variant mapping
 */
export interface StatusBadgeProps {
  status: string;
  className?: string;
  children?: React.ReactNode;
}

export function StatusBadge({ status, className, children }: StatusBadgeProps) {
  const getStatusVariant = (status: string): BadgeVariant => {
    const statusLower = status.toLowerCase();
    if (statusLower === "active" || statusLower === "enabled" || statusLower === "completed") {
      return "success";
    }
    if (statusLower === "inactive" || statusLower === "disabled" || statusLower === "pending") {
      return "default";
    }
    if (statusLower === "warning" || statusLower === "review" || statusLower === "flagged") {
      return "warning";
    }
    if (statusLower === "error" || statusLower === "failed" || statusLower === "blocked") {
      return "danger";
    }
    return "default";
  };

  return (
    <Badge variant={getStatusVariant(status)} className={cn("font-semibold backdrop-blur", className)}>
      {children ?? status}
    </Badge>
  );
}