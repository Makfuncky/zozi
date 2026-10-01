"use client";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ title = "Something went wrong", message, onRetry, className }: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center", className)}>
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-danger/10 mb-4">
        <span className="text-danger text-xl">⚠</span>
      </div>
      <h3 className="text-lg font-semibold text-text mb-1">{title}</h3>
      {message && <p className="text-sm text-text-muted mb-4 max-w-sm">{message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand text-on-brand text-sm font-medium hover:bg-brand-dark transition-colors">
          Try Again
        </button>
      )}
    </div>
  );
}
