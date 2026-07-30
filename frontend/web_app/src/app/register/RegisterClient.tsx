"use client";

import { useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, User, Mail, Lock, CheckCircle2, Loader2 } from "@/lib/icons";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

function CustomerRegisterPage() {
  const router = useRouter();
  const addToast = useToastStore((s) => s.addToast);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
    phone: "",
  });

  const update = (patch: Partial<typeof form>) => setForm((prev) => ({ ...prev, ...patch }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      addToast("Passwords do not match", "error");
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.username,
          email: form.email,
          password: form.password,
          role: "customer",
          full_name: form.full_name || form.username,
          phone: form.phone || null,
        }),
        skipAuthRedirect: true,
      });
      if (!res.ok) {
        const d = await parseJsonResponse(res);
        throw new Error(getErrorMessage(d || {}) || "Registration failed");
      }
      addToast("Account created! Please sign in.", "success");
      router.push("/login");
    } catch (err: any) {
      addToast(err.message || "Registration failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-surface-base px-4 py-16 text-text">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <button
          onClick={() => router.push("/login")}
          className="flex items-center gap-2 text-xs text-text-muted hover:text-text mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to sign in
        </button>

        <div className="text-center mb-8">
          <div className="theme-chip-brand mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl">
            <User className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">Create your account</h1>
          <p className="mt-1 text-sm text-text-muted">Join ZOZI to start shopping</p>
        </div>

        <form onSubmit={handleSubmit} className="theme-card space-y-4 rounded-2xl border p-6">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Username</label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
              <input
                value={form.username}
                onChange={(e) => update({ username: e.target.value })}
                required
                placeholder="username"
                className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Full Name</label>
            <input
              value={form.full_name}
              onChange={(e) => update({ full_name: e.target.value })}
              placeholder="Your name"
              className="theme-input w-full rounded-xl border py-3 px-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Email</label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
              <input
                type="email"
                value={form.email}
                onChange={(e) => update({ email: e.target.value })}
                required
                placeholder="you@email.com"
                className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => update({ password: e.target.value })}
                  required
                  minLength={8}
                  placeholder="••••••••"
                  className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
              <p className="mt-1 text-[10px] text-text-faint">
                Min. 8 chars, with uppercase, lowercase, number &amp; special character.
              </p>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-text-muted">Confirm</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={(e) => update({ confirmPassword: e.target.value })}
                  required
                  placeholder="••••••••"
                  className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-60"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            {submitting ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          Already have an account?{" "}
          <Link href="/login" className="theme-link-brand font-semibold">
            Sign in
          </Link>
        </p>
      </motion.div>
    </main>
  );
}

export default function RegisterClient() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <CustomerRegisterPage />
    </Suspense>
  );
}
