"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Package,
  Clock,
  CheckCircle,
  Truck,
  XCircle,
  ArrowLeft,
  ShoppingBag,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import type { Order } from "@/lib/types";

const STATUS_CONFIG: Record<string, { chip: string; icon: typeof Package; label: string }> = {
  pending: { chip: "theme-chip-warning", icon: Clock, label: "Pending" },
  confirmed: { chip: "theme-chip-info", icon: CheckCircle, label: "Confirmed" },
  processing: { chip: "theme-chip-info", icon: Package, label: "Processing" },
  prepared: { chip: "theme-chip-info", icon: Package, label: "Prepared" },
  picking_up: { chip: "theme-chip-info", icon: Package, label: "Picking Up" },
  shipped: { chip: "theme-chip-success", icon: Truck, label: "Shipped" },
  delivered: { chip: "theme-chip-success", icon: CheckCircle, label: "Delivered" },
  cancelled: { chip: "theme-chip-danger", icon: XCircle, label: "Cancelled" },
  refunded: { chip: "theme-chip-warning", icon: XCircle, label: "Refunded" },
  failed: { chip: "theme-chip-danger", icon: XCircle, label: "Failed" },
};

export default function OrdersPage() {
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const formatPrice = useCurrencyStore((s) => s.format);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    apiFetch("/orders")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        setOrders(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load your orders.");
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

  if (orders.length === 0 && !error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <ShoppingBag className="w-12 h-12 text-primary/30 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text mb-2">No Orders Yet</h2>
          <p className="text-text-faint mb-4 text-xs">
            You haven&apos;t placed any orders yet. Start shopping now!
          </p>
          <button
            onClick={() => router.push("/products")}
            className="theme-btn-primary px-5 py-2.5 text-xs font-bold"
          >
            Browse Products
          </button>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text">My Orders</h1>
          <button
            onClick={() => router.push("/products")}
            className="text-xs text-primary hover:underline font-semibold"
          >
            Continue Shopping
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {orders.map((order, i) => {
            const cfg = STATUS_CONFIG[order.status] ?? STATUS_CONFIG.pending;
            const Icon = cfg.icon;
            const total = order.total_amount ?? order.total ?? 0;
            const itemCount = order.items?.reduce((sum, item) => sum + item.quantity, 0) ?? 0;

            return (
              <motion.div
                key={order.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => router.push(`/orders/${order.id}`)}
                className="p-5 rounded-2xl border border-border bg-surface-1 hover:border-primary/40 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5 text-text-muted" />
                    </div>
                    <div>
                      <p className="font-bold text-text text-sm">Order #{order.id}</p>
                      <p className="text-text-faint text-xs mt-0.5">
                        {order.created_at ? new Date(order.created_at).toLocaleDateString() : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${cfg.chip}`}>
                      {cfg.label}
                    </span>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                  <span className="rounded-full bg-surface-2 px-2.5 py-1 font-semibold text-text">
                    {itemCount} item{itemCount === 1 ? "" : "s"}
                  </span>
                  {order.payment_method && (
                    <span className="rounded-full bg-surface-2 px-2.5 py-1 text-text-muted capitalize">
                      {order.payment_method.replaceAll("_", " ")}
                    </span>
                  )}
                  {order.tracking_number && (
                    <span className="rounded-full bg-surface-2 px-2.5 py-1 text-text-muted font-mono text-[10px]">
                      {order.tracking_number}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between mt-3">
                  {order.tracking_number && (
                    <span className="text-text-faint text-xs font-mono">
                      {order.tracking_number}
                    </span>
                  )}
                  {!order.tracking_number && (
                    <span className="text-text-faint text-xs">
                      {order.shipping_address ? "Delivery pending" : ""}
                    </span>
                  )}
                  <span className="text-text font-bold text-sm">
                    {formatPrice(total)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
