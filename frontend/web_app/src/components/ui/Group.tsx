"use client";
import { cn } from "@/lib/utils";

interface GroupProps {
  children: React.ReactNode; className?: string;
  gap?: "none" | "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around";
  wrap?: boolean;
}

const gapClasses = { none: "gap-0", sm: "gap-1", md: "gap-2", lg: "gap-4" };
const alignClasses = { start: "items-start", center: "items-center", end: "items-end", stretch: "items-stretch" };
const justifyClasses = { start: "justify-start", center: "justify-center", end: "justify-end", between: "justify-between", around: "justify-around" };

export function Group({ children, className, gap = "md", align = "center", justify = "start", wrap = true }: GroupProps) {
  return (
    <div className={cn("flex", gapClasses[gap], alignClasses[align], justifyClasses[justify], wrap && "flex-wrap", className)}>
      {children}
    </div>
  );
}

interface StackProps {
  children: React.ReactNode; className?: string;
  gap?: "none" | "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
}

export function Stack({ children, className, gap = "md", align = "stretch" }: StackProps) {
  return (
    <div className={cn("flex flex-col", gapClasses[gap], alignClasses[align], className)}>
      {children}
    </div>
  );
}
