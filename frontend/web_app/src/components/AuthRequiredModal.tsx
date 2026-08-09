"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  LogIn,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  X,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import {
  apiFetch,
  getErrorMessage,
  parseJsonResponse,
  setAccessToken,
  clearAccessToken,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useAuthModalStore } from "@/lib/authModalStore";

export default function AuthRequiredModal() {
  const isOpen = useAuthModalStore((s) => s.isOpen);
  const mode = useAuthModalStore((s) => s.mode);
  const initialError = useAuthModalStore((s) => s.initialError);
  const setMode = useAuthModalStore((s) => s.setMode);
  const close = useAuthModalStore((s) => s.close);
  const setInitialError = useAuthModalStore((s) => s.setInitialError);
  const consumePendingAction = useAuthModalStore((s) => s.consumePendingAction);
  const { refresh } = useAuth();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Seed the error banner from the store when the modal opens, and clear
  // the store's transient initialError once we've consumed it.
  useEffect(() => {
    if (isOpen) {
      setError(initialError);
      setSuccess(null);
      setLoading(false);
      setShowPassword(false);
    } else if (initialError) {
      setInitialError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, mode]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!identifier.trim() || !password) {
      setError("Please enter your email/username and password.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: identifier.trim(), password }),
        skipAuthRedirect: true,
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        setError(getErrorMessage(data || {}));
        return;
      }
      if (!data?.access_token) {
        setError("Unexpected response from the server. Please try again.");
        return;
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      const user = await refresh(true);
      if (!user) {
        clearAccessToken();
        localStorage.removeItem("zozi_has_session");
        setError("Could not load your account. Please try again.");
        return;
      }
      const action = consumePendingAction();
      if (typeof action === "function") {
        try {
          await action();
        } catch {
          /* ignore pending action errors */
        }
      }
      close();
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!username.trim() || !email.trim() || !password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim(),
          password,
          role: "customer",
          full_name: username.trim(),
        }),
        skipAuthRedirect: true,
      });
      if (!res.ok) {
        const d = await parseJsonResponse(res);
        setError(getErrorMessage(d || {}));
        return;
      }
      setSuccess("Account created! Please sign in with your credentials.");
      setMode("login");
      setIdentifier(email.trim());
      setPassword("");
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[200] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div
            className="absolute inset-0 theme-overlay"
            onClick={close}
            aria-hidden
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            transition={{ type: "spring", damping: 26, stiffness: 320 }}
            className="relative z-10 w-full max-w-md theme-card rounded-2xl border p-6 shadow-2xl"
          >
            <button
              onClick={close}
              aria-label="Close"
              className="absolute right-3 top-3 rounded-full p-2 text-text-muted transition-colors hover:bg-surface-1 hover:text-text"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="mb-5 text-center">
              <div className="theme-chip-brand mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl">
                <LogIn className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-xl font-bold text-text">
                {mode === "login" ? "Welcome back" : "Create your account"}
              </h2>
              <p className="mt-1 text-sm text-text-muted">
                {mode === "login"
                  ? "Sign in to continue to ZOZI"
                  : "Join ZOZI to start shopping"}
              </p>
            </div>

            <div className="mb-5 flex rounded-xl border border-border bg-surface-1 p-1">
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`flex-1 rounded-lg py-2 text-sm font-semibold transition-colors ${
                  mode === "login" ? "bg-primary text-on-brand" : "text-text-muted hover:text-text"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                className={`flex-1 rounded-lg py-2 text-sm font-semibold transition-colors ${
                  mode === "register" ? "bg-primary text-on-brand" : "text-text-muted hover:text-text"
                }`}
              >
                Register
              </button>
            </div>

            {error && (
              <div className="theme-alert-danger mb-4 flex items-center gap-2 rounded-xl p-3 text-sm">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}
            {success && (
              <div className="theme-alert-success mb-4 flex items-center gap-2 rounded-xl p-3 text-sm">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                {success}
              </div>
            )}

            {mode === "login" ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">
                    Email or Username
                  </label>
                  <div className="relative">
                    <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      autoFocus
                      placeholder="you@email.com"
                      className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
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
                      className="theme-input w-full rounded-xl border py-3 pl-10 pr-10 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
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
                  disabled={loading}
                  className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-60"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <LogIn className="h-4 w-4" />
                  )}
                  {loading ? "Signing in…" : "Sign In"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">
                    Username
                  </label>
                  <div className="relative">
                    <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      autoFocus
                      placeholder="username"
                      className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-text-muted">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@email.com"
                      className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                        className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-text-muted">
                      Confirm
                    </label>
                    <div className="relative">
                      <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                      <input
                        type={showPassword ? "text" : "password"}
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        placeholder="••••••••"
                        className="theme-input w-full rounded-xl border py-3 pl-10 pr-4 text-sm placeholder:text-text-faint focus:border-primary focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="theme-btn-primary flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold disabled:opacity-60"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <User className="h-4 w-4" />}
                  {loading ? "Creating account…" : "Create Account"}
                </button>
              </form>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
