"use client";
import { cn } from "@/lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1.5 text-sm", className)}>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span className="text-text-faint">/</span>}
          {item.href && i < items.length - 1 ? (
            <a href={item.href} className="text-text-muted hover:text-text transition-colors">{item.label}</a>
          ) : (
            <span className={cn(i === items.length - 1 ? "text-text font-medium" : "text-text-muted")}>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
