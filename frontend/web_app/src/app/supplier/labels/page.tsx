"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { ScanLine, ArrowRight, Package, Printer, RefreshCw } from "@/lib/icons";

type OrderRow = {
  id: number;
  status?: string;
  created_at?: string;
  items?: Array<{ product_name?: string; quantity?: number }>;
  customer_name?: string;
  total_amount?: number;
};

const STATUS_CHIP: Record<string, string> = {
  pending: "theme-chip-muted",
  paid: "theme-chip-info",
  processing: "theme-chip-info",
  shipped: "theme-chip-brand",
  delivered: "theme-chip-success",
  completed: "theme-chip-success",
  cancelled: "theme-chip-danger",
  refunded: "theme-chip-danger",
  returned: "theme-chip-warning",
};

function statusChip(status?: string): string {
  if (!status) return "theme-chip-muted";
  return STATUS_CHIP[status.toLowerCase()] || "theme-chip-muted";
}

export default function SupplierLabelsPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch("/supplier/orders?limit=100&status=paid,processing,shipped");
      const json = (await parseJsonResponse(res)) as { data?: OrderRow[]; items?: OrderRow[] } | OrderRow[];
      if (!res.ok) {
        throw new Error(getErrorMessage((json as object) || {}));
      }
      const rows = Array.isArray(json)
        ? json
        : ((json as { data?: OrderRow[] }).data ?? (json as { items?: OrderRow[] }).items ?? []);
      setOrders(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SupplierLayout title="Parcel Labels">
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Operations"
          title="Parcel Labels & Packing Slips"
          description="Printable parcel labels and packing slips are generated from each order. Pick an order below to open its printable sheet."
          icon={<ScanLine className="h-5 w-5" />}
          actions={
            <button
              onClick={() => void load()}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          }
        />

        {error ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{error}</p>
            <button
              onClick={() => void load()}
              className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold"
            >
              Retry
            </button>
          </div>
        ) : loading ? (
          <PanelLoadingState count={5} blockClassName="h-16 rounded-xl border border-border bg-surface-1 animate-pulse" />
        ) : orders.length === 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="theme-card rounded-xl border p-5">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-primary/12 p-3 text-primary">
                  <Package className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text">No printable orders yet</p>
                  <p className="text-xs text-text-muted">Orders awaiting fulfilment will appear here.</p>
                </div>
              </div>
              <p className="mt-3 text-xs leading-6 text-text-muted">
                Each order in your fulfilment queue lets you create a parcel record, upload the packed
                parcel photo, and print a professional packing sheet with a scannable label.
              </p>
              <Link
                href="/supplier/orders"
                className="theme-btn-primary mt-4 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold"
              >
                Open Orders
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="theme-card overflow-hidden rounded-xl border">
            <div className="divide-y divide-border">
              {orders.map((order) => {
                const itemCount = order.items?.reduce((sum, item) => sum + (item.quantity ?? 0), 0) ?? 0;
                return (
                  <Link
                    key={order.id}
                    href={`/supplier/labels/${order.id}`}
                    className="flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-text">#{order.id}</span>
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${statusChip(order.status)}`}>
                          {order.status ?? "unknown"}
                        </span>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-text-muted">
                        {order.customer_name ? `For ${order.customer_name} · ` : ""}
                        {itemCount} item{itemCount === 1 ? "" : "s"}
                        {order.created_at ? ` · ${order.created_at.slice(0, 10)}` : ""}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-4">
                      {typeof order.total_amount === "number" && (
                        <span className="hidden text-xs font-semibold text-text tabular-nums sm:inline">
                          {formatMoney(order.total_amount)}
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-surface-1 px-3 py-1.5 text-xs font-semibold text-text-muted">
                        <Printer className="h-3.5 w-3.5" />
                        Print
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
