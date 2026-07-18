"use client";

import { cn } from "@/lib/utils";

type CardVariant = "default" | "elevated" | "interactive";

interface CardProps {
  className?: string;
  variant?: CardVariant;
  children: React.ReactNode;
  as?: "section" | "article" | "div";
}

export function Card({ className, variant = "default", children, as = "div" }: CardProps) {
  const baseClasses = "rounded-xl border transition-all duration-200";
  
  const variantClasses = {
    default: "bg-glass-base border-glass-border",
    elevated: "bg-glass-mid border-glass-border-mid shadow-card",
    interactive: "bg-glass-base border-glass-border hover:bg-glass-hi hover:border-glass-border-mid shadow-card hover:shadow-card-hover",
  };

  const Component = as;

  return (
    <Component className={cn(baseClasses, variantClasses[variant], className)}>
      {children}
    </Component>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4 border-b border-glass-border-mid", className)} role="heading" aria-level={2}>
      {children}
    </div>
  );
}

export function CardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4", className)}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-4 border-t border-glass-border-mid", className)} role="contentinfo">
      {children}
    </div>
  );
}