"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { PackageX, Clock, CheckCircle, XCircle, RotateCcw, RefreshCw } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { ReturnRequest } from "@/lib/types";

const STATUS_CONFIG: Record<string, { chip: string; icon: typeof Clock }> = {
  pending: { chip: "theme-chip-warning", icon: Clock },
  approved: { chip: "theme-chip-info", icon: CheckCircle },
  rejected: { chip: "theme-chip-danger", icon: XCircle },
  completed: { chip: "theme-chip-success", icon: PackageX },
  refunded: { chip: "theme-chip-info", icon: RefreshCw },
};

export default function ReturnsPage() {
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const formatPrice = useCurrencyStore((s) => s.format);
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    apiFetch("/returns")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        setReturns(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load return requests.");
        setLoading(false);
      });
  }, [isLoggedIn, authLoading, router]);

  if (loading || authLoading) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      </main>
    );
  }

  if (returns.length === 0 && !error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <PackageX className="w-12 h-12 text-danger/40 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text mb-2">No Returns Yet</h2>
          <p className="text-text-faint mb-4 text-xs">
            You haven&apos;t submitted any return requests.
          </p>
          <button
            onClick={() => router.push("/orders")}
            className="theme-btn-primary px-5 py-2.5 text-xs font-bold"
          >
            View My Orders
          </button>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text">My Returns</h1>
          <button
            onClick={() => router.push("/orders")}
            className="text-xs text-primary hover:underline font-semibold"
          >
            ? Back to Orders
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {returns.map((ret, i) => {
            const cfg = STATUS_CONFIG[ret.status] ?? STATUS_CONFIG.pending;
            const Icon = cfg.icon;

            return (
              <motion.div
                key={ret.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => router.push(`/returns/${ret.id}`)}
                className="p-5 rounded-2xl border border-border bg-surface-1 hover:border-primary/40 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center shrink-0">
                      <RotateCcw className="w-5 h-5 text-text-muted" />
                    </div>
                    <div>
                      <p className="font-bold text-text text-sm">Return #{ret.id}</p>
                      <p className="text-text-muted text-xs mt-0.5">Order #{ret.order_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Icon className="w-3.5 h-3.5" />
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${cfg.chip}`}>
                      {ret.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                  <span className="rounded-full bg-surface-2 px-2.5 py-1 font-semibold capitalize text-text">
                    {ret.intent}
                  </span>
                  {ret.items?.length ? (
                    <span className="rounded-full bg-surface-2 px-2.5 py-1 text-text-muted">
                      {ret.items.map((item) => `${item.product_name} x${item.quantity}`).join(", ")}
                    </span>
                  ) : null}
                </div>

                <p className="text-text-muted text-xs mt-3 line-clamp-2">{ret.reason}</p>

                <div className="flex items-center justify-between mt-3">
                  <span className="text-text-faint text-xs">
                    {new Date(ret.created_at).toLocaleDateString()}
                  </span>
                  {ret.refund_amount != null && (
                    <span className="text-success text-xs font-bold">
                      Refund: {formatPrice(ret.refund_amount)}
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </main>
  );
}


