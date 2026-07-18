"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, CheckCircle, AlertCircle, Loader2 } from "@/lib/icons";
import { apiFetch } from "@/lib/api";

interface NewsletterSignupProps {
  variant?: "footer" | "hero" | "inline";
  className?: string;
}

export default function NewsletterSignup({ variant = "inline", className = "" }: NewsletterSignupProps) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const response = await apiFetch("/email/newsletter/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          first_name: firstName.trim() || null,
          source: "website"
        }),
      });

      if (response.ok) {
        setMessage({ type: "success", text: "Successfully subscribed! Check your email for confirmation." });
        setEmail("");
        setFirstName("");
      } else {
        const error = await response.json();
        setMessage({ type: "error", text: error.detail || "Failed to subscribe. Please try again." });
      }
    } catch {
      setMessage({ type: "error", text: "Network error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  const variants = {
    footer: {
      container: "theme-card p-6 rounded-2xl",
      title: "text-lg font-semibold text-text mb-2",
      description: "text-sm text-text-muted mb-4",
      form: "space-y-3",
      input: "w-full px-4 py-3 border border-border rounded-xl text-sm bg-surface focus:border-primary focus:outline-none",
      button: "w-full theme-btn-primary px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50"
    },
    hero: {
      container: "theme-card p-8 rounded-2xl border",
      title: "text-2xl font-bold text-text mb-2",
      description: "text-text-muted mb-6",
      form: "space-y-4",
      input: "w-full px-4 py-3 border border-border rounded-xl text-base bg-surface focus:border-primary focus:outline-none",
      button: "w-full theme-btn-primary px-6 py-3 rounded-xl text-base font-semibold disabled:opacity-50"
    },
    inline: {
      container: "theme-card p-4 rounded-2xl",
      title: "text-lg font-semibold text-text mb-2",
      description: "text-sm text-text-muted mb-3",
      form: "flex gap-2",
      input: "flex-1 px-4 py-3 border border-border rounded-xl text-sm bg-surface focus:border-primary focus:outline-none",
      button: "theme-btn-primary px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
    }
  };

  const style = variants[variant];

  return (
    <div className={`${style.container} ${className}`}>
      <div className="text-center">
        <h3 className={style.title}>Stay in Style</h3>
        <p className={style.description}>
          Get exclusive access to new arrivals, special offers, and fashion tips.
        </p>
      </div>

      <form onSubmit={handleSubmit} className={style.form}>
        {variant !== "inline" && (
          <div>
            <input
              type="text"
              placeholder="First name (optional)"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className={style.input}
            />
          </div>
        )}

        <div className={variant === "inline" ? "flex-1" : ""}>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className={style.input}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !email.trim()}
          className={style.button}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {variant === "inline" ? "Subscribing..." : "Subscribe"}
            </>
          ) : (
            <>
              <Mail className="w-4 h-4" />
              Subscribe
            </>
          )}
        </button>
      </form>

      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`mt-3 p-3 rounded-md flex items-center gap-2 text-sm ${
              message.type === "success"
                ? "bg-success/10 text-success border border-success/30"
                : "bg-danger/10 text-danger border border-danger/30"
            }`}
          >
            {message.type === "success" ? (
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
            )}
            {message.text}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


