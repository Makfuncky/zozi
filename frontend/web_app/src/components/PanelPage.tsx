"use client";

import {
  useRef, useState, useEffect, useId, useCallback,
  type ComponentPropsWithoutRef, type ComponentType, type ReactNode,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight, ChevronDown, GripVertical } from "@/lib/icons";
import "@/styles/panel-modern.css";

// ─── Motion Variants ──────────────────────────────────────────

export const ENTER_VARIANTS = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.28, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] },
  }),
};

export const FADE_SCALE = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    transition: { duration: 0.15, ease: "easeIn" },
  },
};

// ─── Stagger entrance animation utility ────────────────────────

export const staggerItems = (delay: number = 0.04) => ({
  hidden: {},
  visible: {
    transition: {
      staggerChildren: delay,
    },
  },
});

// ─── Width System ───────────────────────────────────────────────

type PanelWidth = "full" | "wide" | "roomy" | "medium" | "narrow";

const WIDTH_CLASS_MAP: Record<PanelWidth, string> = {
  full: "mx-auto max-w-7xl space-y-5",
  wide: "mx-auto max-w-5xl space-y-6",
  roomy: "mx-auto max-w-6xl space-y-6",
  medium: "mx-auto max-w-4xl space-y-6",
  narrow: "mx-auto max-w-3xl space-y-6",
};

// ─── PanelContent ───────────────────────────────────────────────

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

// ─── PanelHero ──────────────────────────────────────────────────

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
    <div className={cn("glass-panel rounded-2xl border p-5 sm:p-6", className)}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          {icon && (
            <div className="shrink-0 rounded-2xl bg-primary/12 p-3 text-primary">{icon}</div>
          )}
          <div>
            {eyebrow && (
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">{eyebrow}</p>
            )}
            {title && <div className="mt-1 text-lg font-semibold leading-tight text-text sm:text-[1.35rem]">{title}</div>}
            {description && <div className="mt-1.5 max-w-3xl text-[13px] leading-6 text-text-muted">{description}</div>}
          </div>
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2 self-start lg:justify-end">{actions}</div>}
      </div>
    </div>
  );
}

// ─── PanelTabs (scrollable with arrows) ───────────────────────

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
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
  };

  useEffect(() => {
    updateScrollState();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScrollState);
    const ro = new ResizeObserver(updateScrollState);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", updateScrollState);
      ro.disconnect();
    };
  }, [items]);

  const scroll = (dir: "left" | "right") => {
    scrollRef.current?.scrollBy({ left: dir === "left" ? -200 : 200, behavior: "smooth" });
  };

  return (
    <div className="relative">
      {canScrollLeft && (
        <button onClick={() => scroll("left")}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 flex items-center justify-center
            rounded-full bg-surface border border-border shadow-sm text-text-muted hover:text-text
            transition-colors -ml-3">
          <ChevronLeft className="w-3 h-3" />
        </button>
      )}
      {canScrollRight && (
        <button onClick={() => scroll("right")}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 flex items-center justify-center
            rounded-full bg-surface border border-border shadow-sm text-text-muted hover:text-text
            transition-colors -mr-3">
          <ChevronRight className="w-3 h-3" />
        </button>
      )}
      <div ref={scrollRef}
        className={cn("theme-panel rounded-xl border p-1 overflow-x-auto scrollbar-hide", className)}>
        <div className="flex gap-1 min-w-max">
          {items.map((item) => {
            const Icon = item.icon;
            const active = item.key === value;
            return (
              <button key={item.key} type="button" onClick={() => onChange(item.key)}
                className={cn(
                  "inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-all duration-150 whitespace-nowrap",
                  active
                    ? "theme-btn-primary shadow-none"
                    : "theme-btn-secondary border border-transparent text-text-muted hover:border-border/70 hover:text-text",
                )}>
                {Icon && <Icon className="h-3.5 w-3.5" />}
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── PanelLoadingState ─────────────────────────────────────────

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
        <div key={index} className={cn(blockClassName, "transition-all")}
          style={{ animationDelay: `${index * 0.1}s` }} />
      ))}
    </PanelContent>
  );
}

// ─── PanelAnimate ───────────────────────────────────────────────

interface PanelAnimateProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /**
   * Animation variant:
   * - "fadeUp": fades in and slides up (default, great for cards in a grid)
   * - "fadeScale": fades and scales in (great for modals/drawers)
   */
  variant?: "fadeUp" | "fadeScale";
}

export function PanelAnimate({ children, className, delay = 0, variant = "fadeUp" }: PanelAnimateProps) {
  return (
    <motion.div
      className={className}
      variants={variant === "fadeScale" ? FADE_SCALE : ENTER_VARIANTS}
      initial="hidden"
      animate="visible"
      exit={variant === "fadeScale" ? "exit" : undefined}
      custom={delay}
    >
      {children}
    </motion.div>
  );
}

// ─── PanelStagger (container that staggers entrance of children) ─

interface PanelStaggerProps {
  children: ReactNode;
  className?: string;
  staggerDelay?: number;
}

export function PanelStagger({ children, className, staggerDelay = 0.04 }: PanelStaggerProps) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

// ─── PanelCard ─────────────────────────────────────────────────

interface PanelCardProps {
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  hover?: boolean;
  onClick?: () => void;
}

const CARD_PADDING = { none: "p-0", sm: "p-3", md: "p-5", lg: "p-6" };

export function PanelCard({ children, className, padding = "md", hover, onClick }: PanelCardProps) {
  return (
    <div className={cn(
      "panel-card glass-panel rounded-2xl border transition-all duration-150",
      CARD_PADDING[padding],
      hover && "hover:shadow-lg hover:-translate-y-0.5 cursor-pointer",
      onClick && "cursor-pointer",
      className,
    )} onClick={onClick}>
      {children}
    </div>
  );
}

// ─── PanelCard.Header / PanelCard.Body / PanelCard.Footer ────

PanelCard.Header = function PanelCardHeader({
  children, className, action,
}: { children: ReactNode; className?: string; action?: ReactNode }) {
  return (
    <div className={cn("flex items-center justify-between gap-3 mb-3", className)}>
      <div className="font-semibold text-text text-sm">{children}</div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};

PanelCard.Body = function PanelCardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("text-sm text-text", className)}>{children}</div>;
};

PanelCard.Footer = function PanelCardFooter({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("border-t border-border mt-4 pt-4 flex items-center gap-2", className)}>{children}</div>;
};

// ─── CollapsiblePanelCard ───────────────────────────────────────

interface CollapsiblePanelCardProps {
  children: ReactNode;
  className?: string;
  title: string;
  /** Unique key for this collapsible section (persisted via usePanelLayout) */
  panelKey: string;
  /**
   * Whether the panel is expanded. Pass from usePanelLayout.
   * If omitted, the panel uses internal state (no persistence).
   */
  expanded?: boolean;
  /** Callback when toggle is clicked. Pass from usePanelLayout. */
  onToggle?: () => void;
  /** Optional count badge shown next to the title */
  count?: number;
  /** Optional icon shown before the title */
  icon?: ReactNode;
  /** Optional action buttons shown in the header (e.g. "Add new") */
  actions?: ReactNode;
  /** Compact mode — smaller padding, smaller text */
  compact?: boolean;
  /** Default expanded state when using internal state */
  defaultExpanded?: boolean;
}

export function CollapsiblePanelCard({
  children,
  className,
  title,
  panelKey,
  expanded: controlledExpanded,
  onToggle,
  count,
  icon,
  actions,
  compact = false,
  defaultExpanded = true,
}: CollapsiblePanelCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);
  const isControlled = controlledExpanded !== undefined && onToggle !== undefined;
  const expanded = isControlled ? controlledExpanded : internalExpanded;
  const handleToggle = useCallback(() => {
    if (isControlled) onToggle();
    else setInternalExpanded((v) => !v);
  }, [isControlled, onToggle]);

  const id = useId();
  const bodyId = `panel-body-${panelKey}-${id}`;

  return (
    <div className={cn(
      "collapsible-panel glass-panel rounded-2xl border transition-all duration-150",
      compact ? "p-3" : "p-4",
      className,
    )}>
      {/* Header — always visible, clickable to toggle */}
      <button
        type="button"
        onClick={handleToggle}
        aria-expanded={expanded}
        aria-controls={bodyId}
        className="collapsible-header flex w-full items-center justify-between gap-3 cursor-pointer"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Drag handle */}
          <GripVertical className="h-3.5 w-3.5 text-text-faint/40 shrink-0" />
          {/* Icon */}
          {icon && <span className="text-primary shrink-0">{icon}</span>}
          {/* Title */}
          <span className={cn(
            "font-semibold text-text truncate",
            compact ? "text-xs" : "text-sm",
          )}>
            {title}
          </span>
          {/* Count badge */}
          {count !== undefined && (
            <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-primary/10 text-[10px] font-bold text-primary px-1.5 shrink-0">
              {count > 99 ? "99+" : count}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Custom actions */}
          {actions}
          {/* Chevron toggle */}
          <motion.div
            animate={{ rotate: expanded ? 0 : -90 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="p-1 rounded-md hover:bg-surface-2 text-text-muted hover:text-text transition-colors"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </motion.div>
        </div>
      </button>

      {/* Collapsible body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id={bodyId}
            key="body"
            initial={{ height: 0, opacity: 0, overflow: "hidden" }}
            animate={{ height: "auto", opacity: 1, overflow: "visible" }}
            exit={{ height: 0, opacity: 0, overflow: "hidden" }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="collapsible-body"
          >
            <div className={cn(compact ? "mt-3 space-y-2" : "mt-4 space-y-3")}>
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── PanelCompactStatCard ───────────────────────────────────────

interface PanelCompactStatCardProps {
  label: string;
  value: string | number;
  icon?: ComponentType<{ className?: string }>;
  trend?: { value: string; positive?: boolean };
  color?: string;
  onClick?: () => void;
  className?: string;
  /** Ultra-compact variation: minimal padding, smaller text */
  ultraCompact?: boolean;
}

export function PanelCompactStatCard({
  label, value, icon: Icon, trend, color, onClick, className, ultraCompact = false,
}: PanelCompactStatCardProps) {
  return (
    <motion.div
      onClick={onClick}
      whileHover={onClick ? { y: -2, scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      className={cn(
        "panel-compact-stat glass-panel rounded-xl border transition-all duration-150",
        ultraCompact ? "p-2.5" : "p-3",
        onClick && "cursor-pointer",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <p className={cn(
          "font-semibold text-text tabular-nums leading-none",
          ultraCompact ? "text-sm" : "text-base",
        )}>{value}</p>
        {Icon && (
          <div className={cn(
            "flex items-center justify-center shrink-0",
            color ? `text-${color}` : "text-text-muted",
            ultraCompact ? "w-6 h-6" : "w-7 h-7",
          )}>
            <Icon className={ultraCompact ? "w-3 h-3" : "w-3.5 h-3.5"} />
          </div>
        )}
      </div>
      <div className="flex items-center gap-1.5 mt-1">
        <span className={cn(
          "text-text-muted",
          ultraCompact ? "text-[10px]" : "text-xs",
        )}>{label}</span>
        {trend && (
          <span className={cn(
            "inline-flex items-center gap-0.5 font-medium",
            ultraCompact ? "text-[9px]" : "text-[10px]",
            trend.positive ? "text-success" : "text-danger",
          )}>
            {trend.positive ? "↑" : "↓"}{trend.value}
          </span>
        )}
      </div>
    </motion.div>
  );
}

// ─── PanelGrid ──────────────────────────────────────────────────

interface PanelGridProps {
  children: ReactNode;
  className?: string;
  cols?: 1 | 2 | 3 | 4 | 5 | 6;
  gap?: "sm" | "md" | "lg";
}

const GRID_COLS = { 1: "grid-cols-1", 2: "grid-cols-1 sm:grid-cols-2", 3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3", 4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4", 5: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5", 6: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6" };
const GRID_GAP = { sm: "gap-2", md: "gap-4", lg: "gap-6" };

export function PanelGrid({ children, className, cols = 3, gap = "md" }: PanelGridProps) {
  return <div className={cn("grid", GRID_COLS[cols], GRID_GAP[gap], className)}>{children}</div>;
}

// ─── PanelSection ───────────────────────────────────────────────

interface PanelSectionProps {
  children: ReactNode;
  title?: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
  padded?: boolean;
}

export function PanelSection({ children, title, description, action, icon, className, padded = true }: PanelSectionProps) {
  return (
    <section className={cn(padded && "space-y-4", className)}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            {icon && <span className="text-primary flex-shrink-0">{icon}</span>}
            <div>
              {title && <h2 className="text-sm font-semibold text-text">{title}</h2>}
              {description && <p className="text-xs text-text-muted mt-0.5">{description}</p>}
            </div>
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

// ─── PanelStatCard ──────────────────────────────────────────────

interface PanelStatCardProps {
  label: string;
  value: string | number;
  description?: string;
  icon?: ComponentType<{ className?: string }>;
  trend?: { value: string; positive?: boolean };
  color?: string;
  subtitle?: string;
  onClick?: () => void;
  className?: string;
}

export function PanelStatCard({ label, value, icon: Icon, trend, color, subtitle, onClick, className, description }: PanelStatCardProps) {
  return (
    <div onClick={onClick}
      className={cn(
        "glass-panel rounded-2xl border p-5 transition-all duration-150",
        onClick && "cursor-pointer hover:shadow-lg hover:-translate-y-0.5",
        className,
      )}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-text-muted uppercase tracking-wider">{label}</p>
        {Icon && (
          <div className={cn(
            "w-9 h-9 rounded-xl flex items-center justify-center",
            color ? `bg-gradient-to-br ${color}` : "bg-primary/10",
          )}>
            <Icon className={cn("w-4.5 h-4.5", color ? "text-white" : "text-primary")} />
          </div>
        )}
      </div>
      <p className="text-2xl font-bold text-text">{value}</p>
      {subtitle && <p className="text-xs text-text-muted mt-1">{subtitle}</p>}
      {trend && (
        <div className={cn(
          "inline-flex items-center gap-1 mt-2 text-xs font-medium",
          trend.positive ? "text-success" : "text-danger",
        )}>
          <span>{trend.positive ? "↑" : "↓"}</span>
          <span>{trend.value}</span>
        </div>
      )}
    </div>
  );
}

// ─── PanelMetric ────────────────────────────────────────────────

interface PanelMetricProps {
  label: string;
  value: string | number;
  icon?: ComponentType<{ className?: string }>;
  trend?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function PanelMetric({ label, value, icon: Icon, trend, className, size = "md" }: PanelMetricProps) {
  const sizeClasses = { sm: "text-lg", md: "text-2xl", lg: "text-4xl" };
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {Icon && (
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-primary" />
        </div>
      )}
      <div>
        <p className={cn("font-bold text-text", sizeClasses[size])}>{value}</p>
        <p className="text-xs text-text-muted">{label}</p>
        {trend && <p className="text-[11px] text-success mt-0.5">{trend}</p>}
      </div>
    </div>
  );
}

// ─── PanelFilterBar ─────────────────────────────────────────────

interface PanelFilterBarProps {
  children: ReactNode;
  className?: string;
}

export function PanelFilterBar({ children, className }: PanelFilterBarProps) {
  return (
    <div className={cn(
      "flex flex-wrap items-center gap-2 p-3 rounded-xl border border-border bg-surface-1",
      className,
    )}>
      {children}
    </div>
  );
}

// ─── PanelActionBar ─────────────────────────────────────────────

interface PanelActionBarProps {
  children: ReactNode;
  className?: string;
  position?: "left" | "right" | "center";
}

export function PanelActionBar({ children, className, position = "right" }: PanelActionBarProps) {
  const alignClasses = { left: "justify-start", right: "justify-end", center: "justify-center" };
  return (
    <div className={cn(
      "flex items-center gap-2 flex-wrap",
      alignClasses[position],
      className,
    )}>
      {children}
    </div>
  );
}

// ─── PanelDivider ───────────────────────────────────────────────

interface PanelDividerProps {
  className?: string;
  label?: string;
}

export function PanelDivider({ className, label }: PanelDividerProps) {
  if (label) {
    return (
      <div className={cn("flex items-center gap-3", className)}>
        <div className="flex-1 h-px bg-border" />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-text-faint flex-shrink-0">{label}</span>
        <div className="flex-1 h-px bg-border" />
      </div>
    );
  }
  return <div className={cn("h-px bg-border", className)} />;
}

// ─── PanelBreadcrumb ────────────────────────────────────────────

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PanelBreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function PanelBreadcrumb({ items, className }: PanelBreadcrumbProps) {
  return (
    <nav className={cn("flex items-center gap-1.5 text-xs text-text-muted", className)}>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span className="text-text-faint">/</span>}
          {item.href ? (
            <a href={item.href} className="hover:text-text transition-colors">{item.label}</a>
          ) : (
            <span className="text-text font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

// ─── PanelDrawer ────────────────────────────────────────────────

interface PanelDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  className?: string;
  side?: "left" | "right";
}

export function PanelDrawer({ isOpen, onClose, children, title, className, side = "right" }: PanelDrawerProps) {
  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm transition-opacity"
          onClick={onClose} />
      )}
      <div className={cn(
        "fixed top-0 bottom-0 z-50 w-full max-w-lg bg-surface border-l border-border shadow-2xl transition-transform duration-300 ease-out",
        side === "left" ? "left-0" : "right-0",
        isOpen ? "translate-x-0" : side === "left" ? "-translate-x-full" : "translate-x-full",
        className,
      )}>
        {title && (
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h3 className="font-semibold text-text">{title}</h3>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-1 text-text-muted">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        <div className="overflow-y-auto h-full pb-20">{children}</div>
      </div>
    </>
  );
}
