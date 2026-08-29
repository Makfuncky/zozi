"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Info, AlertTriangle, X } from "lucide-react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const TOAST_ICONS: Record<ToastType, React.ElementType> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
};

const TOAST_COLORS: Record<ToastType, string> = {
  success: "border-success/30 bg-success/10",
  error: "border-error/30 bg-error/10",
  info: "border-info/30 bg-info/10",
  warning: "border-warning/30 bg-warning/10",
};

const TOAST_ICON_COLORS: Record<ToastType, string> = {
  success: "text-success",
  error: "text-error",
  info: "text-info",
  warning: "text-warning",
};

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const Icon = TOAST_ICONS[toast.type];

  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, toast.duration ?? 4000);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg backdrop-blur-sm ${TOAST_COLORS[toast.type]}`}
    >
      <Icon className={`w-5 h-5 shrink-0 ${TOAST_ICON_COLORS[toast.type]}`} />
      <p className="text-sm font-medium text-text-primary flex-1">{toast.message}</p>
      <button
        onClick={() => onDismiss(toast.id)}
        className="p-1 rounded-lg hover:bg-surface-2 transition-colors shrink-0"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4 text-text-faint" />
      </button>
    </motion.div>
  );
}

export default function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div className="fixed top-20 right-4 z-[200] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem toast={toast} onDismiss={onDismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}
