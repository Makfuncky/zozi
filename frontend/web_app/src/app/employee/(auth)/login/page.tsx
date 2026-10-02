"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Key, AlertCircle, Briefcase, User, Lock, Eye, EyeOff } from "@/lib/icons";
import { apiFetch, getErrorMessage, parseJsonResponse, setAccessToken, clearAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

export default function EmployeeLoginPage() {
  const router = useRouter();
  const { refresh, user, isLoading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    router.prefetch("/employee/dashboard");
  }, [router]);

  useEffect(() => {
    if (isLoading || user?.role !== "employee") {
      return;
    }
    router.replace("/employee/dashboard");
  }, [isLoading, router, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        skipAuthRedirect: true,
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        setError(getErrorMessage(data || {}));
        setLoading(false);
        return;
      }
      if (!data?.access_token) {
        setError("Network error — please try again.");
        setLoading(false);
        return;
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      const user = await refresh(true);
      if (!user) {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError("Network error — please try again.");
        return;
      }
      if (user.role !== "employee") {
        setError("This account does not have employee access.");
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setLoading(false);
        return;
      }
      router.push("/employee/dashboard");
    } catch {
      setError("Network error — please try again.");
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
            <Briefcase className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">Employee Login</h1>
          <p className="mt-1 text-sm text-text-muted">Sign in to access your employee workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="theme-card space-y-5 rounded-2xl border p-6">
          {error && (
            <div className="theme-alert-danger flex items-center gap-2 rounded-xl p-3 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Email or Username</label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="employee@zozi.com"
                type="text"
                autoComplete="username"
                required
                className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
              />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">Password</label>
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
            disabled={loading || !username || !password}
            className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl text-sm font-bold disabled:opacity-50"
          >
            {loading ? (
              <div className="h-4 w-4 rounded-full border-2 border-on-brand/30 border-t-on-brand animate-spin" />
            ) : (
              <Key className="w-4 h-4" />
            )}
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>
      </motion.div>
    </main>
  );
}
