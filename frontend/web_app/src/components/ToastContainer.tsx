"use client";

import { useToastStore } from "@/lib/toastStore";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const STYLES = {
  error: {
    bg: "bg-danger/15 border-danger/30",
    text: "text-danger",
    Icon: AlertCircle,
  },
  success: {
    bg: "bg-success/15 border-success/30",
    text: "text-success",
    Icon: CheckCircle,
  },
  info: {
    bg: "bg-info/15 border-info/30",
    text: "text-info",
    Icon: Info,
  },
  warning: {
    bg: "bg-warning/15 border-warning/30",
    text: "text-warning",
    Icon: AlertCircle,
  },
} as const;

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const remove = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 flex flex-col gap-1.5 z-200">
      <AnimatePresence>
        {toasts.map((t) => {
          const style = STYLES[t.type as keyof typeof STYLES] || STYLES.info;
          const IconComp = style.Icon;
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              className={`max-w-72 w-full rounded-xl border p-3 shadow-lg backdrop-blur-sm flex items-start gap-2.5 bg-glass-mid ${style.bg}`}
            >
              <IconComp className={`w-4 h-4 shrink-0 mt-0.5 ${style.text}`} />
              <p className={`text-xs font-medium flex-1 ${style.text}`}>
                {t.message}
              </p>
              <button
                onClick={() => remove(t.id)}
                className="shrink-0 text-text-faint transition-colors hover:text-text"
              >
                <X className="w-3 h-3" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}


