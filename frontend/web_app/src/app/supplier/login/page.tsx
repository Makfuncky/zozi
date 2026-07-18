"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { LogIn, AlertCircle, Store } from "lucide-react";
import { apiFetch, getErrorMessage, parseJsonResponse, setAccessToken, clearAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

export default function SupplierLoginPage() {
  const router = useRouter();
  const { refresh, user, isLoading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    router.prefetch("/supplier/dashboard");
  }, [router]);

  useEffect(() => {
    if (isLoading || user?.role !== "supplier") {
      return;
    }
    router.replace("/supplier/dashboard");
  }, [isLoading, router, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body = new URLSearchParams({ username, password });
      const res = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
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
        setError("Network error");
        setLoading(false);
        return;
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      const user = await refresh(true);
      if (!user) {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError("Network error");
        return;
      }
      if (user.role !== "supplier") {
        setError("This account is not a supplier account.");
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setLoading(false);
        return;
      }
      router.push("/supplier/dashboard");
    } catch {
      setError("Network error");
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
            <Store className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">Supplier Login</h1>
          <p className="mt-1 text-sm text-text-muted">
            Access your supplier dashboard
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="theme-card space-y-5 rounded-2xl border p-6"
        >
          {error && (
            <div className="theme-alert-danger flex items-center gap-2 rounded-xl p-3 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">
              Username
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Username"
              className="theme-input w-full rounded-xl border px-4 py-3 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="theme-input w-full rounded-xl border px-4 py-3 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-50"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-on-brand/30 border-t-on-brand rounded-full animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          No supplier account?{" "}
          <Link
            href="/supplier/register"
            className="theme-link-brand font-semibold"
          >
            Register
          </Link>
        </p>
      </motion.div>
    </main>
  );
}


