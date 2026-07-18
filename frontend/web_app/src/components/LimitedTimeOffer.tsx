"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, Percent } from "lucide-react";
import { useLocaleStore } from "@/lib/localeStore";

export default function LimitedTimeOffer() {
  const tr = useLocaleStore((s) => s.t);
  const [isVisible, setIsVisible] = useState(true);
  const [deadline] = useState(() => Date.now() + 24 * 60 * 60 * 1000);
  const [timeLeft, setTimeLeft] = useState(() => Math.max(0, Math.ceil((deadline - Date.now()) / 1000))); // 24 hours in seconds

  useEffect(() => {
    const syncTime = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") {
        return;
      }
      setTimeLeft((prev) => {
        const next = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        return prev === next ? prev : next;
      });
    };

    syncTime();
    const timer = window.setInterval(syncTime, 1000);
    document.addEventListener("visibilitychange", syncTime);

    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", syncTime);
    };
  }, [deadline]);

  useEffect(() => {
    if (timeLeft <= 0) {
      setIsVisible(false);
    }
  }, [timeLeft]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="theme-bg-brand-to-brand-light text-white overflow-hidden"
      >
        <div className="max-w-11xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Percent className="w-5 h-5" />
              <span className="font-semibold">{tr("limitedOfferBanner")}</span>
              <div className="flex items-center gap-1 text-sm">
                <Clock className="w-4 h-4" />
                <span className="font-mono">{formatTime(timeLeft)}</span>
              </div>
            </div>
            <button
              onClick={() => setIsVisible(false)}
              className="rounded-full p-1 transition-colors hover:bg-white/15"
              aria-label={tr("closeOfferBanner")}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}


