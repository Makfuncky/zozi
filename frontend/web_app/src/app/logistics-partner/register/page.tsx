"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { AlertCircle, Truck, UserPlus } from "lucide-react";
import { getErrorMessage } from "@/lib/api";
import Logo from "@/components/Logo";

const AUTH_PROXY_URL = "/api/auth/register";

const structuredFieldProps = {
  autoCapitalize: "none" as const,
  autoCorrect: "off" as const,
  spellCheck: false,
};

export default function LogisticsPartnerRegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm: "",
    phone: "",
    termsAccepted: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (key: keyof typeof form) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.type === "checkbox"
        ? event.target.checked
        : event.target.value;
      setForm((current) => ({ ...current, [key]: value }));
    };

  const validate = (): string => {
    if (!form.username.trim()) return "Username is required";
    if (!/^[a-zA-Z0-9_]{3,30}$/.test(form.username)) {
      return "Username: 3-30 chars, letters/numbers/underscore only";
    }
    if (!form.email.trim()) return "Email is required";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      return "Please enter a valid email address";
    }
    if (form.password.length < 8) return "Password must be at least 8 characters";
    if (form.password !== form.confirm) return "Passwords do not match";
    if (form.phone && !/^\+?[\d\s\-().]{7,20}$/.test(form.phone)) {
      return "Enter a valid phone number";
    }
    if (!form.termsAccepted) return "You must accept the Terms & Conditions to register";
    return "";
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await fetch(AUTH_PROXY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.username.trim(),
          email: form.email.trim().toLowerCase(),
          password: form.password,
          phone: form.phone.trim() || undefined,
          role: "logistics_partner",
          terms_accepted: true,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(getErrorMessage(data));
        setLoading(false);
        return;
      }

      router.push("/logistics-partner/login?registered=1");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "theme-input w-full rounded-xl border px-4 py-3 text-sm focus:border-primary focus:outline-none transition-colors placeholder:text-text-faint";

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-base px-4 py-12 text-text">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center"><Logo size="lg" /></div>
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl theme-chip-brand">
            <Truck className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">Create Logistics Account</h1>
          <p className="mt-1 text-sm text-text-muted">
            Register your logistics partner access for deliveries and shipment updates
          </p>
        </div>

        <form onSubmit={handleSubmit} className="theme-card space-y-5 rounded-2xl border p-6">
          {error && (
            <div className="theme-alert-danger flex items-center gap-2 rounded-xl p-3 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Username</label>
            <input
              value={form.username}
              onChange={set("username")}
              required
              placeholder="Choose a username"
              autoComplete="username"
              {...structuredFieldProps}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={set("email")}
              required
              placeholder="partner@company.com"
              autoComplete="email"
              inputMode="email"
              {...structuredFieldProps}
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Phone</label>
            <input
              value={form.phone}
              onChange={set("phone")}
              placeholder="+971 50 000 0000"
              autoComplete="tel"
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={set("password")}
              required
              placeholder="••••••••"
              autoComplete="new-password"
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Confirm Password</label>
            <input
              type="password"
              value={form.confirm}
              onChange={set("confirm")}
              required
              placeholder="••••••••"
              autoComplete="new-password"
              className={inputClass}
            />
          </div>

          <label className="flex items-start gap-3 rounded-xl border border-border px-4 py-3 text-sm text-text-muted">
            <input
              type="checkbox"
              checked={form.termsAccepted}
              onChange={set("termsAccepted")}
              className="mt-0.5"
            />
            <span>I agree to the Terms & Conditions for logistics partner onboarding.</span>
          </label>

          <button
            type="submit"
            disabled={loading}
            className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-50"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-on-brand/30 border-t-on-brand" />
            ) : (
              <UserPlus className="h-4 w-4" />
            )}
            {loading ? "Creating account…" : "Register"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          Already have a logistics account?{" "}
          <Link href="/logistics-partner/login" className="theme-link-brand font-semibold">
            Sign In
          </Link>
        </p>
      </motion.div>
    </main>
  );
}


