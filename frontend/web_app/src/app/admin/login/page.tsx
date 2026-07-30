"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Crown, LogIn, AlertCircle } from "lucide-react";
import { apiFetch, getErrorMessage, parseJsonResponse, setAccessToken, clearAccessToken } from "@/lib/api";
import { useLocaleStore } from "@/lib/localeStore";
import { useAuth } from "@/lib/useAuth";

const MotionDiv = motion.div as any;

const STAFF_ROLES = new Set(["admin", "sub_admin", "moderator", "support"]);

export default function AdminLoginPage() {
  const router = useRouter();
  const { refresh, user, isLoading } = useAuth();
  const tr = useLocaleStore((s) => s.t);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoading || !user || !STAFF_ROLES.has(user.role)) {
      return;
    }
    router.replace("/admin/dashboard");
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
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        setError(getErrorMessage(data || {}));
        setLoading(false);
        return;
      }
      if (!data?.access_token) {
        setError(tr("networkError"));
        setLoading(false);
        return;
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      const user = await refresh(true);
      if (!user) {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError(tr("networkError"));
        return;
      }
      if (!STAFF_ROLES.has(user.role)) {
        setError(tr("adminStaffOnly"));
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setLoading(false);
        return;
      }
      router.push("/admin/dashboard");
    } catch {
      setError(tr("networkError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-surface-base px-4 py-16 text-text">
      <MotionDiv
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="theme-chip-brand mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl">
            <Crown className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-text">{tr("adminAccess")}</h1>
          <p className="mt-1 text-sm text-text-muted">
            {tr("staffCredentialsRequired")}
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
              {tr("username")}
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder={tr("usernamePlaceholder")}
              className="theme-input w-full rounded-xl border px-4 py-3 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-text-muted">
              {tr("password")}
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
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-on-brand/30 border-t-on-brand" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {loading ? tr("signingIn") : tr("signIn")}
          </button>
        </form>
      </MotionDiv>
    </main>
  );
}


