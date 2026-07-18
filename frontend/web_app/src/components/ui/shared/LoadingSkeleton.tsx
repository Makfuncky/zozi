"use client";

import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  lines?: number;
  className?: string;
}

export function LoadingSkeleton({ lines = 3, className }: LoadingSkeletonProps) {
  return (
    <div className={cn("animate-pulse", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div 
          key={i} 
          className={cn(
            "bg-glass-mid rounded-lg",
            i === 0 ? "h-4" : "h-3",
            i === lines - 1 ? "mb-0" : "mb-2"
          )} 
        />
      ))}
    </div>
  );
}

interface LoadingCardProps {
  className?: string;
}

export function LoadingCard({ className }: LoadingCardProps) {
  return (
    <div className={cn("glass-panel rounded-xl border border-glass-border-mid p-4 animate-pulse", className)}>
      <div className="h-4 bg-glass-solid rounded mb-3" />
      <div className="h-3 bg-glass-solid rounded mb-2" />
      <div className="h-3 bg-glass-solid rounded w-3/4" />
    </div>
  );
}

interface LoadingTableProps {
  rows?: number;
  className?: string;
}

export function LoadingTable({ rows = 5, className }: LoadingTableProps) {
  return (
    <div className={cn("animate-pulse", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div 
          key={i} 
          className={cn(
            "flex items-center",
            i === 0 ? "mb-2" : "mb-1",
            i === rows - 1 ? "mb-0" : ""
          )}
        >
          <div className="h-3 bg-glass-mid rounded" style={{ width: `${80 + Math.random() * 20}%` }} />
        </div>
      ))}
    </div>
  );
}