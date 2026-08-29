"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, Check, X } from "lucide-react";

interface StockAlertProps {
  productId: number;
  productName: string;
  isOutOfStock: boolean;
}

export default function StockAlert({ productId, productName, isOutOfStock }: StockAlertProps) {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const [open, setOpen] = useState(false);

  if (!isOutOfStock) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail("");
    }
  };

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-primary transition-colors"
      >
        <Bell className="w-4 h-4" />
        Notify me when back in stock
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            {subscribed ? (
              <div className="mt-3 p-3 rounded-lg bg-success/10 border border-success/20 flex items-center gap-2">
                <Check className="w-4 h-4 text-success" />
                <span className="text-sm text-success">
                  We&apos;ll notify you when this item is back in stock.
                </span>
                <button
                  onClick={() => setSubscribed(false)}
                  className="ml-auto p-1 rounded hover:bg-success/20"
                  aria-label="Dismiss"
                >
                  <X className="w-3 h-3 text-success" />
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-surface-2 border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-sm text-text-primary"
                  required
                />
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary-dark transition-colors"
                >
                  Notify Me
                </button>
              </form>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
