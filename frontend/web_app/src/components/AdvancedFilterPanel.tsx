"use client";

import { Button } from "@/components/ui/Button";

import { ReactNode, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SlidersHorizontal, RotateCcw, X } from "@/lib/icons";

interface Props {
  /** Number of active (non-default) filters to show as a badge */
  activeCount?: number;
  /** Whether the filter panel dropdown is expanded */
  open: boolean;
  /** Toggle expand/collapse */
  onToggle: () => void;
  /** Reset all filters to defaults */
  onReset: () => void;
  /** Preset quick-apply chips rendered below the fields row */
  presets?: Array<{ label: string; onClick: () => void }>;
  /** The filter inputs (label + controls) rendered inside the panel */
  children: ReactNode;
  /** Alignment of the dropdown relative to its trigger button */
  align?: "left" | "right";
  /** Additional class names on the trigger button */
  triggerClassName?: string;
}

/**
 * AdvancedFilterPanel
 *
 * A reusable dropdown shell for advanced filter controls.
 * Usage: wrap the individual filter inputs as `children` and pass `presets`
 * for quick-apply chips. The component manages open/close, shows an active
 * filter badge, and provides a "Reset all" action.
 *
 * @example
 * <AdvancedFilterPanel
 *   activeCount={activeFiltersCount}
 *   open={showFilters}
 *   onToggle={() => setShowFilters(v => !v)}
 *   onReset={resetAllFilters}
 *   presets={[{ label: "This week", onClick: applyThisWeek }]}
 * >
 *   <label>Min amount <input .../></label>
 * </AdvancedFilterPanel>
 */
export default function AdvancedFilterPanel({
  activeCount = 0,
  open,
  onToggle,
  onReset,
  presets,
  children,
  align = "left",
  triggerClassName,
}: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) onToggle();
    };
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open, onToggle]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onToggle();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onToggle]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-haspopup="true"
        className={`relative inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition-colors ${
          open || activeCount > 0
            ? "border-primary bg-primary/10 text-primary"
            : "border-border bg-surface-1 text-text-muted hover:bg-surface-2 hover:text-text"
        } ${triggerClassName ?? ""}`}
      >
        <SlidersHorizontal className="h-3.5 w-3.5" />
        Filters
        {activeCount > 0 && (
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-on-brand">
            {activeCount > 9 ? "9+" : activeCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.14 }}
            className={`glass-dropdown absolute top-full z-[999] mt-2 w-max min-w-80 max-w-lg rounded-2xl p-4 ${
              align === "right" ? "right-0" : "left-0"
            }`}
          >
            {/* Panel header */}
            <div className="mb-3 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">
                Filters
                {activeCount > 0 && (
                  <span className="ml-2 rounded-full bg-primary/15 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                    {activeCount} active
                  </span>
                )}
              </p>
              <div className="flex items-center gap-1">
                {activeCount > 0 && (
                  <button
                    type="button"
                    onClick={onReset}
                    className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Reset all
                  </button>
                )}
                <button
                  type="button"
                  onClick={onToggle}
                  aria-label="Close filter panel"
                  className="rounded-lg p-1 text-text-faint transition-colors hover:bg-surface-2 hover:text-text"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Filter fields */}
            <div className="space-y-3">{children}</div>

            {/* Quick-apply presets */}
            {presets && presets.length > 0 && (
              <div className="mt-3 border-t border-border pt-3">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">
                  Quick presets
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {presets.map((preset) => (
                    <Button variant="primary" className="rounded-lg border border-border bg-surface-1 px-2.5 py-1.5 text-xs font-medium text-text-muted transition-colors hover:text-primary" key={preset.label}
                      type="button"
                      onClick={() => { preset.onClick(); onToggle(); }}
                    >
                      {preset.label}
                    </Button>
                  ))}
                  {activeCount > 0 && (
                    <Button variant="danger" className="rounded-lg border border-border bg-surface-1 px-2.5 py-1.5 text-xs font-medium text-danger/70 transition-colors hover:text-danger" type="button"
                      onClick={() => { onReset(); onToggle(); }}
                    >
                      Reset all
                    </Button>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


