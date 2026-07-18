"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Lock, CheckCircle, Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import BrandLoading from "@/components/BrandLoading";

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams?.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (!token) {
      setError("No reset token found. Use the link from your email.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch("/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (res.ok) {
        setDone(true);
        setTimeout(() => router.push("/login"), 3000);
      } else {
        setError(data.detail || "Reset failed. The link may have expired.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-base px-4 text-text">
      <div className="theme-card w-full max-w-sm rounded-2xl border p-8">
        {done ? (
          <div className="text-center">
            <CheckCircle className="theme-status-success mx-auto mb-4 h-12 w-12" />
            <h1 className="mb-2 text-lg font-bold text-text">Password Reset!</h1>
            <p className="mb-4 text-sm text-text-muted">
              Your password has been updated. Redirecting to login…
            </p>
            <Link
              href="/login"
              className="theme-btn-primary inline-block rounded-xl px-6 py-2.5 text-sm font-bold"
            >
              Sign In Now
            </Link>
          </div>
        ) : (
          <>
            <h1 className="mb-1 text-xl font-bold text-text">Reset Password</h1>
            <p className="mb-6 text-sm text-text-muted">Enter your new password.</p>

            {error && (
              <div className="theme-alert-danger mb-4 rounded-xl p-3 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-faint" />
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    required
                    minLength={8}
                    onChange={(e) => setPassword(e.target.value)}
                    className="theme-input w-full rounded-xl border py-2.5 pl-9 pr-10 text-sm focus:border-primary focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"
                  >
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="mt-1 text-[10px] text-text-faint">
                  At least 8 characters with a number and uppercase letter.
                </p>
              </div>

              <div>
                <label className="mb-1 block text-[11px] font-semibold text-text-muted">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-faint" />
                  <input
                    type={showPw ? "text" : "password"}
                    value={confirm}
                    required
                    onChange={(e) => setConfirm(e.target.value)}
                    className="theme-input w-full rounded-xl border py-2.5 pl-9 pr-3 text-sm focus:border-primary focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="theme-btn-primary w-full rounded-xl py-2.5 text-sm font-bold disabled:opacity-50"
              >
                {loading ? "Resetting…" : "Reset Password"}
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <BrandLoading fullscreen label="Loading reset form..." className="bg-surface-base" />
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}


