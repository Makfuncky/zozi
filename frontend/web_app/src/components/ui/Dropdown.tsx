"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface DropdownProps {
  /** Render-prop / element that toggles the menu. Receives current open state. */
  trigger: (open: boolean) => ReactNode;
  children: (close: () => void) => ReactNode;
  align?: "left" | "right";
  className?: string;
  menuClassName?: string;
  /** Animation origin, used for the pop-in transform. */
  side?: "bottom" | "top";
  ariaLabel?: string;
}

/**
 * Consistent popover / dropdown used across the app.
 * - Glass surface via the shared `.glass-dropdown` class
 * - Closes on outside-click and on Escape
 * - Proper ARIA: the menu has role="menu", the trigger toggles aria-expanded
 */
export function Dropdown({
  trigger,
  children,
  align = "left",
  className,
  menuClassName,
  side = "bottom",
  ariaLabel,
}: DropdownProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const close = () => setOpen(false);

  return (
    <div ref={rootRef} className={cn("relative inline-block", className)}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        aria-label={ariaLabel}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center"
      >
        {trigger(open)}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            id={menuId}
            role="menu"
            initial={{ opacity: 0, y: side === "bottom" ? -6 : 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: side === "bottom" ? -6 : 6, scale: 0.98 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
            className={cn(
              "glass-dropdown absolute z-[999] mt-2 min-w-[12rem] rounded-2xl p-1.5 shadow-2xl",
              align === "right" ? "right-0" : "left-0",
              side === "top" && "bottom-full mb-2 mt-0",
              menuClassName
            )}
          >
            {children(close)}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export interface DropdownItemProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  danger?: boolean;
}

export function DropdownItem({ children, onClick, className, danger }: DropdownItemProps) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors",
        danger
          ? "text-danger hover:bg-danger/10"
          : "text-text hover:bg-surface-2",
        className
      )}
    >
      {children}
    </button>
  );
}
