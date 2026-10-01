"use client";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { X } from "@/lib/icons";
interface DrawerProps { isOpen: boolean; onClose: () => void; title?: string; children: React.ReactNode; side?: "left" | "right"; size?: "sm" | "md" | "lg"; }
const sideClasses = { left: "left-0 border-l", right: "right-0 border-r" };
const sizeClasses = { sm: "w-80", md: "w-96", lg: "w-[28rem]" };
export function Drawer({ isOpen, onClose, title, children, side = "right", size = "md" }: DrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-modal theme-overlay" onClick={onClose} />
          <motion.div initial={{ x: side === "right" ? "100%" : "-100%" }} animate={{ x: 0 }}
            exit={{ x: side === "right" ? "100%" : "-100%" }}
            transition={{ type: "spring", damping: 24, stiffness: 200 }}
            className={cn("fixed top-0 bottom-0 glass-panel border shadow-2xl flex flex-col", sideClasses[side], sizeClasses[size])}
          >
            {title && (
              <div className="flex items-center justify-between p-4 border-b border-glass-border-mid">
                <h3 className="text-sm font-bold text-text">{title}</h3>
                <button onClick={onClose} className="text-text-muted hover:text-text rounded-lg p-1" aria-label="Close drawer">
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto p-4">{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
