"use client";
import { useState, useRef, useEffect, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface PopoverProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "left" | "right" | "center";
  side?: "bottom" | "top";
  className?: string;
}

export function Popover({ trigger, children, align = "left", side = "bottom", className }: PopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const alignClasses = { left: "left-0", right: "right-0", center: "left-1/2 -translate-x-1/2" };
  const sideClasses = { bottom: "top-full mt-2", top: "bottom-full mb-2" };

  return (
    <div className={cn("relative inline-flex", className)} ref={ref}>
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: side === "bottom" ? -4 : 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: side === "bottom" ? -4 : 4 }}
            transition={{ duration: 0.15 }}
            className={cn("absolute z-popover w-72 rounded-xl border border-glass-border-mid bg-glass-strong shadow-xl p-4", alignClasses[align], sideClasses[side])}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
