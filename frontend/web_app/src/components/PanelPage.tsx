"use client";

import type { ComponentPropsWithoutRef, ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";

type PanelWidth = "full" | "wide" | "roomy" | "medium" | "narrow";

const WIDTH_CLASS_MAP: Record<PanelWidth, string> = {
  full: "mx-auto max-w-7xl space-y-5",
  wide: "mx-auto max-w-5xl space-y-6",
  roomy: "mx-auto max-w-6xl space-y-6",
  medium: "mx-auto max-w-4xl space-y-6",
  narrow: "mx-auto max-w-3xl space-y-6",
};

export function PanelContent({
  children,
  width = "full",
  className,
  ...props
}: {
  children?: ReactNode;
  width?: PanelWidth;
  className?: string;
} & ComponentPropsWithoutRef<"div">) {
  return <div className={cn(WIDTH_CLASS_MAP[width], className)} {...props}>{children}</div>;
}

export function PanelHero({
  eyebrow,
  title,
  description,
  icon,
  actions,
  className,
}: {
  eyebrow?: string;
  title?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("theme-card rounded-xl border p-4 sm:p-5", className)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          {icon ? (
            <div className="shrink-0 rounded-2xl bg-primary/12 p-3 text-primary">{icon}</div>
          ) : null}
          <div>
            {eyebrow ? (
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">{eyebrow}</p>
            ) : null}
            {title ? <div className="mt-1 text-lg font-semibold leading-tight text-text sm:text-[1.35rem]">{title}</div> : null}
            {description ? <div className="mt-1.5 max-w-3xl text-[13px] leading-6 text-text-muted">{description}</div> : null}
          </div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2 self-start lg:justify-end">{actions}</div> : null}
      </div>
    </div>
  );
}

export function PanelTabs<T extends string>({
  items,
  value,
  onChange,
  className,
}: {
  items: ReadonlyArray<{ key: T; label: string; icon?: ComponentType<{ className?: string }> }>;
  value: T;
  onChange: (value: T) => void;
  className?: string;
}) {
  return (
    <div className={cn("theme-panel rounded-xl border p-1", className)}>
      <div className="flex flex-wrap gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = item.key === value;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onChange(item.key)}
              className={cn(
                "inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
                isActive
                  ? "theme-btn-primary shadow-none"
                  : "theme-btn-secondary border border-transparent text-text-muted hover:border-border/70 hover:text-text",
              )}
            >
              {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
              {item.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function PanelLoadingState({
  count = 3,
  width = "full",
  className,
  blockClassName = "h-24 rounded-xl bg-surface-2 animate-pulse",
}: {
  count?: number;
  width?: PanelWidth;
  className?: string;
  blockClassName?: string;
}) {
  return (
    <PanelContent width={width} className={className}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className={blockClassName} />
      ))}
    </PanelContent>
  );
}
