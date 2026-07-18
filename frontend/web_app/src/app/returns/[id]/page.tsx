"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, PackageX } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { ReturnRequest } from "@/lib/types";

const STATUS_CONFIG: Record<string, { bg: string; text: string; border: string }> = {
  pending:  { bg: "bg-warning/10",  text: "text-warning",  border: "border-warning/30" },
  approved: { bg: "bg-info/10",     text: "text-info",     border: "border-info/30" },
  rejected: { bg: "bg-danger/10",   text: "text-danger",   border: "border-danger/30" },
  completed:{ bg: "bg-success/10",  text: "text-success",  border: "border-success/30" },
  refunded: { bg: "bg-violet-500/10", text: "text-violet-400", border: "border-violet-500/30" },
};

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-border last:border-0">
      <span className="text-text-muted text-xs">{label}</span>
      <span className="text-text text-xs font-semibold">{value}</span>
    </div>
  );
}

export default function ReturnDetailPage() {
  const params = useParams<{ id: string }>();
  const { id } = params ?? {};
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const formatPrice = useCurrencyStore((s) => s.format);

  const [returnData, setReturnData] = useState<ReturnRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    if (!id) return;
    apiFetch(`/returns/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        setReturnData(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Return not found or you don't have access.");
        setLoading(false);
      });
  }, [id, isLoggedIn, authLoading, router]);

  if (loading || authLoading) {
    return (
      <main className="min-h-screen px-4 py-8">
        <div className="max-w-2xl mx-auto space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      </main>
    );
  }

  if (error || !returnData) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <PackageX className="w-12 h-12 text-danger/40 mx-auto mb-4" />
          <p className="text-danger text-sm">{error ?? "Return not found."}</p>
          <button onClick={() => router.push("/returns")} className="mt-4 text-brand text-xs underline">
            Back to Returns
          </button>
        </div>
      </main>
    );
  }

  const cfg = STATUS_CONFIG[returnData.status] ?? STATUS_CONFIG.pending;

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <button
          onClick={() => router.push("/returns")}
          className="flex items-center gap-1.5 text-text-muted hover:text-text text-xs mb-5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Returns
        </button>

        <h1 className="text-2xl font-bold text-text mb-6">Return #{returnData.id}</h1>

        {/* Status banner */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-2xl border mb-5 text-center ${cfg.bg} ${cfg.border}`}
        >
          <p className={`text-sm font-bold tracking-wide ${cfg.text}`}>
            {returnData.status.toUpperCase()}
          </p>
          {returnData.refund_amount != null && (
            <p className="text-success font-bold text-lg mt-1">
              Refund: {formatPrice(returnData.refund_amount)}
            </p>
          )}
        </motion.div>

        {/* Details card */}
        <div className="p-5 rounded-2xl border border-border bg-surface-1 mb-4">
          <InfoRow label="Return ID" value={`#${returnData.id}`} />
          <InfoRow label="Order ID" value={`#${returnData.order_id}`} />
          <InfoRow label="Request Type" value={returnData.intent === "replacement" ? "Replacement" : "Return for refund"} />
          {returnData.return_window_days != null && (
            <InfoRow label="Window" value={`${returnData.return_window_days}-day policy`} />
          )}
          {returnData.delivered_at && (
            <InfoRow label="Delivered" value={new Date(returnData.delivered_at).toLocaleDateString()} />
          )}
          {returnData.return_deadline && (
            <InfoRow label="Eligible Until" value={new Date(returnData.return_deadline).toLocaleDateString()} />
          )}
          <InfoRow label="Submitted" value={new Date(returnData.created_at).toLocaleDateString()} />
          {returnData.updated_at && (
            <InfoRow label="Last Updated" value={new Date(returnData.updated_at).toLocaleDateString()} />
          )}
        </div>

        {/* Reason */}
        <div className="p-5 rounded-2xl border border-border bg-surface-1 mb-4">
          <p className="text-text-muted text-xs font-semibold uppercase tracking-wider mb-2">Reason</p>
          <p className="text-text text-sm leading-relaxed">{returnData.reason}</p>
        </div>

        {/* Admin notes */}
        {(returnData.resolution_notes || returnData.notes) && (
          <div className="p-5 rounded-2xl border border-info/20 bg-info/5 mb-4">
            <p className="text-info text-xs font-semibold uppercase tracking-wider mb-2">Notes from Support</p>
            <p className="text-text text-sm leading-relaxed">
              {returnData.resolution_notes ?? returnData.notes}
            </p>
          </div>
        )}

        {/* Items */}
        {returnData.items && returnData.items.length > 0 && (
          <div className="p-5 rounded-2xl border border-border bg-surface-1">
            <p className="text-text-muted text-xs font-semibold uppercase tracking-wider mb-3">Items</p>
            <div className="space-y-2">
              {returnData.items.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-text text-sm flex-1">
                    {item.product_name ?? `Product #${item.product_id}`}
                  </span>
                  {item.quantity != null && (
                    <span className="text-text-muted text-xs mr-4">×{item.quantity}</span>
                  )}
                  {item.price != null && (
                    <span className="text-text-muted text-xs">{formatPrice(item.price)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
