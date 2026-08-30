"use client";

import { cn } from "@/lib/utils";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "base" | "panel" | "solid" | "mid" | "hi";
  as?: "div" | "section" | "article";
}

const variantClasses = {
  base: "glass-base",
  panel: "glass-panel",
  solid: "glass-solid",
  mid: "glass-mid",
  hi: "glass-hi",
};

export function GlassCard({ children, className, variant = "panel", as = "div" }: GlassCardProps) {
  const Component = as;
  return (
    <Component
      className={cn(
        "rounded-2xl border transition-all duration-200",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </Component>
  );
}

export function GlassCardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4 border-b border-glass-border-mid", className)}>
      {children}
    </div>
  );
}

export function GlassCardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4", className)}>
      {children}
    </div>
  );
}

export function GlassCardFooter({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4 border-t border-glass-border-mid", className)}>
      {children}
    </div>
  );
}