"use client";
import { cn } from "@/lib/utils";
interface SectionProps { children: React.ReactNode; title?: string; description?: string; className?: string; contentClassName?: string; }
export function Section({ children, title, description, className, contentClassName }: SectionProps) {
  return (
    <section className={cn("mb-8", className)}>
      {(title || description) && (
        <div className="mb-4">
          {title && <h2 className="text-lg font-semibold text-text">{title}</h2>}
          {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
        </div>
      )}
      <div className={cn(contentClassName)}>{children}</div>
    </section>
  );
}
