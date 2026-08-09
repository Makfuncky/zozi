"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { LogIn, AlertCircle, User, Lock, Eye, EyeOff, Loader2 } from "lucide-react";
import {
  apiFetch,
  getErrorMessage,
  parseJsonResponse,
  setAccessToken,
  clearAccessToken,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

function CustomerLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/";
  const { refresh, user, isLoading } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && user?.role === "customer") {
      router.replace(redirectTo);
    }
  }, [isLoading, user, router, redirectTo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!identifier.trim() || !password) {
      setError("Please enter your email/username and password.");
      return;
    }
    setLoading(true);
    try {
      const body = JSON.stringify({ username: identifier.trim(), password });
      const res = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        skipAuthRedirect: true,
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        setError(getErrorMessage(data || {}));
        setLoading(false);
        return;
      }
      if (!data?.access_token) {
        setError("Unexpected response from the server. Please try again.");
        setLoading(false);
        return;
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      const loggedInUser = await refresh(true);
      if (!loggedInUser) {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError("Could not load your account. Please try again.");
        setLoading(false);
        return;
      }
      if (loggedInUser.role !== "customer") {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError("This login is for customer accounts only. Please use the correct portal.");
        setLoading(false);
        return;
      }
      router.push(redirectTo);
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-base px-4 py-16 text-text">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="theme-chip-brand mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl">
            <LogIn className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">Customer Sign In</h1>
          <p className="mt-1 text-sm text-text-muted">
            Welcome back — sign in to your ZOZI account
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="theme-card space-y-5 rounded-2xl border p-6"
        >
          {error && (
            <div className="theme-alert-danger flex items-center gap-2 rounded-xl p-3 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">
              Email or Username
            </label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
              <input
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="you@email.com"
                required
                className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="theme-input w-full rounded-xl border py-3 pl-10 pr-10 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-faint hover:text-text"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !identifier.trim() || !password}
            className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          New to ZOZI?{" "}
          <Link href="/register" className="theme-link-brand font-semibold">
            Create an account
          </Link>
        </p>
        <p className="mt-2 text-center text-sm text-text-muted">
          Are you a seller or logistics partner?{" "}
          <Link href="/supplier/login" className="theme-link-brand font-semibold">
            Supplier
          </Link>{" "}
          ·{" "}
          <Link href="/logistics-partner/login" className="theme-link-brand font-semibold">
            Logistics
          </Link>
        </p>
      </motion.div>
    </main>
  );
}

export default function LoginClient() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <CustomerLoginPage />
    </Suspense>
  );
}
