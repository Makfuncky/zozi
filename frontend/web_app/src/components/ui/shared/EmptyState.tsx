"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";
import { Shield } from "@/lib/icons";

interface EmptyStateProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className 
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center glass-panel rounded-xl border border-glass-border-mid",
      className
    )}>
      <Icon className="h-12 w-12 text-text-faint opacity-40 mb-4" />
      <h3 className="text-sm font-semibold text-text mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-text-faint mb-4 max-w-sm">{description}</p>
      )}
      {action}
    </div>
  );
}

interface EmptyTableProps {
  title?: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyTable({ 
  title = "No data available", 
  description, 
  action 
}: EmptyTableProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4 text-center glass-panel rounded-xl border border-glass-border-mid">
      <Shield className="h-8 w-8 text-text-faint opacity-40 mb-2" />
      <p className="text-xs text-text-faint">{title}</p>
      {description && (
        <p className="text-[10px] text-text-faint mt-1">{description}</p>
      )}
      {action}
    </div>
  );
}