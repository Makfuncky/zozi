"use client";

import { useEffect, useState, use } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Package,
  Clock,
  CheckCircle,
  Truck,
  XCircle,
  MapPin,
  ArrowLeft,
  RefreshCw,
  Hash,
  CreditCard,
  RotateCcw,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { Order, OrderItem, OrderTracking } from "@/lib/types";
import { useCurrencyStore } from "@/lib/currencyStore";

const MapView = dynamic(() => import("@/components/map/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[200px] items-center justify-center rounded-xl border border-border bg-surface-2 text-xs text-text-faint">
      Loading map…
    </div>
  ),
});

const TERMINAL_STATUSES = new Set(["cancelled", "failed", "refunded"]);

const TERMINAL_STATUS_CLASS: Record<string, string> = {
  cancelled: "theme-chip-danger",
  failed: "theme-chip-danger",
  refunded: "theme-chip-warning",
};

function TrackingTimeline({
  orderStatus,
  timeline,
}: {
  orderStatus: string;
  timeline: OrderTracking["timeline"];
}) {
  const isTerminal = TERMINAL_STATUSES.has(orderStatus);

  if (isTerminal) {
    const label =
      orderStatus === "cancelled"
        ? "Order Cancelled"
        : orderStatus === "refunded"
        ? "Refund Processed"
        : "Payment Failed";
    return (
      <div className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold ${TERMINAL_STATUS_CLASS[orderStatus] || "theme-chip-danger"}`}>
        <XCircle className={`h-4 w-4 ${orderStatus === "refunded" ? "theme-status-warning" : "theme-status-danger"}`} />
        {label}
      </div>
    );
  }

  const iconForStep = (key: string) => {
    switch (key) {
      case "placed":
        return Clock;
      case "preparing":
        return Package;
      case "picked_up":
        return CheckCircle;
      case "in_transit":
        return Truck;
      case "delivered":
        return Package;
      default:
        return Clock;
    }
  };

  return (
    <div className="flex items-start gap-0">
      {timeline.map((step, idx) => {
        const done = step.completed;
        const active = step.active;
        const StepIcon = iconForStep(step.key);
        const isLast = idx === timeline.length - 1;

        return (
          <div key={step.key} className="flex items-center flex-1 min-w-0">
            <div className="flex shrink-0 flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors ${
                  done
                    ? "bg-success border-success"
                    : active
                    ? "bg-primary/20 border-primary"
                    : "bg-surface-2 border-border"
                }`}
              >
                <StepIcon
                  className={`w-3.5 h-3.5 ${
                    done ? "text-on-brand" : active ? "theme-status-info" : "text-text-faint"
                  }`}
                />
              </div>
              <span
                className={`text-[10px] mt-1 text-center leading-tight whitespace-nowrap ${
                  done ? "theme-status-success" : active ? "theme-status-info font-semibold" : "text-text-faint"
                }`}
              >
                {step.label}
              </span>
            </div>
            {!isLast && (
              <div
                className={`flex-1 h-0.5 mb-4 mx-1 transition-colors ${
                  done ? "bg-success" : active ? "bg-primary/40" : "bg-border"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function OrderDetailPage({ params }: PageProps) {
  const { id: orderId } = use(params);
  const router = useRouter();
  const { isLoggedIn, isLoading: authLoading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [trackingError, setTrackingError] = useState("");
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState("");
  const [showReturnForm, setShowReturnForm] = useState(false);
  const [returnIntent, setReturnIntent] = useState<"return" | "replacement">("return");
  const [selectedReturnScope, setSelectedReturnScope] = useState("order");
  const [returnReason, setReturnReason] = useState("");
  const [returning, setReturning] = useState(false);
  const [returnSuccess, setReturnSuccess] = useState(false);
  const [returnError, setReturnError] = useState("");
  const formatPrice = useCurrencyStore((s) => s.format);

  useEffect(() => {
    if (!order?.items?.length) return;
    const singleItemId = order.items.length === 1 ? order.items[0].id : undefined;
    setSelectedReturnScope(singleItemId ? `item:${singleItemId}` : "order");
  }, [order?.id, order?.items]);

  const itemLabel = (item: OrderItem) => item.product_name || item.product?.name || `Product #${item.product_id}`;

  const selectedReturnItemId = selectedReturnScope.startsWith("item:")
    ? Number(selectedReturnScope.replace("item:", ""))
    : null;
  const selectedTrackingItem = tracking?.items?.find((item) => item.order_item_id === selectedReturnItemId) ?? null;
  const selectedOrderItem = order?.items?.find((item) => item.id === selectedReturnItemId) ?? null;
  const selectedReturnWindowDays = selectedTrackingItem?.return_window_days
    ?? selectedOrderItem?.product?.return_window_days
    ?? tracking?.return_eligibility?.return_window_days
    ?? 10;
  const returnDeadline = tracking?.return_eligibility?.deadline ? new Date(tracking.return_eligibility.deadline) : null;
  const deliveryDate = tracking?.return_eligibility?.delivered_at ? new Date(tracking.return_eligibility.delivered_at) : null;

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    Promise.all([
      apiFetch(`/orders/${orderId}`),
      apiFetch(`/orders/${orderId}/tracking`),
    ])
      .then(async ([orderResponse, trackingResponse]) => {
        const orderData = orderResponse.ok ? ((await orderResponse.json()) as Order) : null;
        const trackingData = trackingResponse.ok ? ((await trackingResponse.json()) as OrderTracking) : null;
        setOrder(orderData);
        setTracking(trackingData);
        if (!trackingResponse.ok) {
          setTrackingError("Live tracking is not available for this order yet.");
        }
      })
      .catch(() => {
        setTrackingError("Live tracking is not available for this order yet.");
      })
      .finally(() => setLoading(false));
  }, [isLoggedIn, authLoading, orderId, router]);

  const handleCancel = async () => {
    if (!order) return;
    setCancelError("");
    setCancelling(true);
    try {
      const res = await apiFetch(`/orders/${order.id}/cancel`, { method: "POST" });
      if (!res.ok) {
        const d = await res.json();
        setCancelError(d.detail || "Could not cancel order");
      } else {
        const updated = await res.json();
        setOrder(updated);
      }
    } catch {
      setCancelError("Failed to cancel order");
    } finally {
      setCancelling(false);
    }
  };

  const handleReturn = async () => {
    if (!order || !returnReason.trim()) return;
    setReturnError("");
    setReturning(true);
    try {
      const res = await apiFetch("/returns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: order.id,
          order_item_id: selectedReturnItemId ?? undefined,
          intent: returnIntent,
          reason: returnReason.trim(),
        }),
      });
      if (!res.ok) {
        const d = await res.json();
        setReturnError(d.detail || "Could not submit return request");
      } else {
        const createdReturn = await res.json();
        setTracking((prev) => prev ? {
          ...prev,
          active_return_request: {
            id: createdReturn.id,
            order_item_id: createdReturn.order_item_id ?? null,
            intent: createdReturn.intent,
            status: createdReturn.status,
            reason: createdReturn.reason,
            resolution_notes: createdReturn.resolution_notes ?? null,
            items: createdReturn.items ?? [],
            created_at: createdReturn.created_at,
            updated_at: createdReturn.updated_at,
          },
        } : prev);
        setReturnSuccess(true);
        setShowReturnForm(false);
      }
    } catch {
      setReturnError("Failed to submit return request");
    } finally {
      setReturning(false);
    }
  };

  if (loading || authLoading) {
    return (
      <main className="min-h-screen">
        <div className="max-w-2xl mx-auto px-4 py-8 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-surface-2 animate-pulse" />
          ))}
        </div>
      </main>
    );
  }

  if (!order) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Package className="w-10 h-10 text-primary/30 mx-auto mb-3" />
          <p className="text-text-muted text-sm">Order not found</p>
          <button
            onClick={() => router.push("/orders")}
            className="theme-link-brand mt-3 text-xs"
          >
            Back to Orders
          </button>
        </div>
      </main>
    );
  }

  const canCancel = order.status === "pending" || order.status === "confirmed";
  const canReturn = order.status === "delivered";
  const total = order.total_amount ?? (order as unknown as { total?: number }).total ?? 0;
  const activeReturnRequest = tracking?.active_return_request;
  const hasSpecificReturnSelection = selectedReturnItemId !== null;
  const returnScopeLabel = selectedTrackingItem
    ? `${selectedTrackingItem.product_name} x${selectedTrackingItem.quantity}`
    : "All eligible items in this order";

  return (
    <main className="min-h-screen">
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Back + header */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/orders")}
            className="p-1.5 rounded-lg text-text-faint hover:text-text hover:bg-surface-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-sm font-bold text-text">Order #{order.id}</h1>
            <p className="text-[11px] text-text-faint">
              {order.created_at ? new Date(order.created_at).toLocaleString() : ""}
            </p>
          </div>
        </div>

        {/* Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="theme-card border rounded-2xl p-4"
        >
          <h2 className="text-[11px] font-bold text-text-faint uppercase tracking-wide mb-4">
            Order Status
          </h2>
          {tracking ? (
            <div className="space-y-3">
              <div className="inline-flex rounded-lg bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                {tracking.order_status_label || tracking.order_status}
              </div>
              <TrackingTimeline orderStatus={tracking.order_status} timeline={tracking.timeline} />
            </div>
          ) : (
            <div className="rounded-xl border border-border/70 bg-surface-2/40 px-3 py-2 text-xs text-text-muted">
              {trackingError || "Tracking details are not available yet."}
            </div>
          )}
        </motion.div>

        {/* Items */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="theme-card border rounded-2xl p-4"
        >
          <h2 className="text-[11px] font-bold text-text-faint uppercase tracking-wide mb-3">
            Items
          </h2>
          <div className="space-y-2">
            {order.items?.map((item, i) => (
              <div key={i} className="flex justify-between items-center text-xs">
                <span className="text-text-muted">
                  {itemLabel(item)}{" "}
                  <span className="text-text-faint">× {item.quantity}</span>
                </span>
                <span className="font-semibold text-text">
                  {formatPrice(item.price * item.quantity)}
                </span>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-sm font-bold text-text border-t border-border pt-2 mt-3">
            <span>Total</span>
            <span>{formatPrice(total)}</span>
          </div>
        </motion.div>

        {/* Shipping + tracking */}
        {(tracking?.shipping_address || order.shipping_address || tracking?.shipments?.length || order.tracking_number) && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="theme-card border rounded-2xl p-4 space-y-2"
          >
            <h2 className="text-[11px] font-bold text-text-faint uppercase tracking-wide mb-1">
              Delivery
            </h2>
            {(tracking?.shipping_address || order.shipping_address) && (
              <div className="flex items-start gap-2 text-xs text-text-muted">
                <MapPin className="theme-status-info mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{tracking?.shipping_address || order.shipping_address}</span>
              </div>
            )}
            {(tracking?.delivery_location || order.delivery_location) && (
              <MapView
                location={tracking?.delivery_location || order.delivery_location}
                height="180px"
                markerLabel="Delivery"
                markerColor="#e11d48"
              />
            )}
            {(tracking?.tracking_numbers?.[0] || order.tracking_number) && (
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <Hash className="theme-status-info h-3.5 w-3.5 shrink-0" />
                <span>Tracking: <span className="text-text font-mono">{tracking?.tracking_numbers?.[0] || order.tracking_number}</span></span>
              </div>
            )}
            {tracking?.shipments?.length ? (
              <div className="mt-2 space-y-2 border-t border-border pt-3">
                {tracking.shipments.map((shipment) => (
                  <div key={shipment.id} className="rounded-xl border border-border/60 bg-surface-2/40 p-3 text-xs text-text-muted">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-semibold text-text">
                        Shipment #{shipment.id}
                        {shipment.supplier_name ? ` · ${shipment.supplier_name}` : ""}
                      </span>
                      <span className="rounded-lg bg-primary/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-primary">
                        {shipment.status_label || shipment.status.replaceAll("_", " ")}
                      </span>
                    </div>
                    <div className="mt-2 space-y-1">
                      {shipment.carrier_name && <p>Carrier: <span className="text-text">{shipment.carrier_name}</span></p>}
                      {shipment.current_hub && <p>Current hub: <span className="text-text">{shipment.current_hub}</span></p>}
                      {shipment.distribution_channel && <p>Channel: <span className="text-text">{shipment.distribution_channel.replaceAll("_", " ")}</span></p>}
                      {shipment.scan_code && <p>QR / Scan Code: <span className="font-mono text-text">{shipment.scan_code}</span></p>}
                      {shipment.estimated_delivery && (
                        <p>Estimated delivery: <span className="text-text">{new Date(shipment.estimated_delivery).toLocaleString()}</span></p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </motion.div>
        )}

        {/* Payment info */}
        {(order.paid_at || order.payment_intent_id) && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="theme-card border rounded-2xl p-4 space-y-2"
          >
            <h2 className="text-[11px] font-bold text-text-faint uppercase tracking-wide mb-1">
              Payment
            </h2>
            {order.paid_at && (
              <div className="theme-status-success flex items-center gap-2 text-xs">
                <CheckCircle className="h-3.5 w-3.5" />
                <span>Paid on {new Date(order.paid_at).toLocaleString()}</span>
              </div>
            )}
            {order.payment_intent_id && (
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <CreditCard className="theme-status-info h-3.5 w-3.5 shrink-0" />
                <span className="font-mono text-[10px] truncate">{order.payment_intent_id}</span>
              </div>
            )}
          </motion.div>
        )}

        {/* Return section */}
        {canReturn && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.17 }}
            className="theme-card border rounded-2xl p-4"
          >
            <div className="mb-3 rounded-xl border border-border/70 bg-surface-2/40 p-3 text-xs text-text-muted">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-text">Return policy</p>
                <span className="rounded-full bg-primary/10 px-2 py-1 text-[10px] font-semibold text-primary">
                  {selectedReturnWindowDays}-day window
                </span>
              </div>
              <p className="mt-2">
                {hasSpecificReturnSelection ? `${itemLabel(selectedOrderItem ?? { product_id: selectedTrackingItem?.product_id ?? 0, quantity: selectedTrackingItem?.quantity ?? 0, price: selectedTrackingItem?.price ?? 0, product_name: selectedTrackingItem?.product_name } as OrderItem)} follows a ${selectedReturnWindowDays}-day return window.` : `This delivered order is eligible under the longest configured item window of ${selectedReturnWindowDays} days.`}
              </p>
              {deliveryDate ? (
                <p className="mt-1">
                  Delivered on <span className="font-semibold text-text">{deliveryDate.toLocaleDateString()}</span>
                  {returnDeadline ? (
                    <>
                      {" "}and eligible until <span className="font-semibold text-text">{returnDeadline.toLocaleDateString()}</span>
                      {typeof tracking?.return_eligibility?.days_remaining === "number" ? ` (${Math.max(tracking.return_eligibility.days_remaining, 0)} day${Math.abs(tracking.return_eligibility.days_remaining) === 1 ? "" : "s"} remaining)` : ""}.
                    </>
                  ) : "."}
                </p>
              ) : null}
            </div>

            {returnSuccess ? (
              <div className="flex items-center gap-2 text-success text-xs font-semibold">
                <CheckCircle className="w-4 h-4" />
                {returnIntent === "replacement" ? "Replacement request submitted." : "Return request submitted."} We&apos;ll review it shortly.
                <button
                  onClick={() => router.push("/returns")}
                  className="ml-auto theme-link-brand text-xs underline"
                >
                  View Returns
                </button>
              </div>
            ) : activeReturnRequest ? (
              <div className="space-y-2 text-xs text-text-muted">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-text">Active {activeReturnRequest.intent}</span>
                  <span className="rounded-full bg-warning/15 px-2 py-1 font-semibold uppercase tracking-wide text-warning">
                    {activeReturnRequest.status.replaceAll("_", " ")}
                  </span>
                </div>
                {activeReturnRequest.items?.length ? (
                  <p>
                    Scope: <span className="text-text">{activeReturnRequest.items.map((item) => `${item.product_name} x${item.quantity}`).join(", ")}</span>
                  </p>
                ) : null}
                <p>
                  Reason: <span className="text-text">{activeReturnRequest.reason}</span>
                </p>
                <button
                  onClick={() => router.push("/returns")}
                  className="theme-link-brand text-xs underline"
                >
                  View return status
                </button>
              </div>
            ) : showReturnForm ? (
              <div className="space-y-3">
                <p className="text-[11px] font-bold text-text-faint uppercase tracking-wide">Request a Return</p>
                {returnError && (
                  <p className="theme-status-danger text-xs">{returnError}</p>
                )}
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="text-xs text-text-muted">
                    <span className="mb-1 block font-semibold text-text">Request type</span>
                    <select
                      value={returnIntent}
                      onChange={(e) => setReturnIntent(e.target.value as "return" | "replacement")}
                      className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-text focus:outline-none focus:border-brand/60"
                    >
                      <option value="return">Return for refund</option>
                      <option value="replacement">Replacement</option>
                    </select>
                  </label>
                  <label className="text-xs text-text-muted">
                    <span className="mb-1 block font-semibold text-text">Item scope</span>
                    <select
                      value={selectedReturnScope}
                      onChange={(e) => setSelectedReturnScope(e.target.value)}
                      className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-text focus:outline-none focus:border-brand/60"
                    >
                      <option value="order">All eligible items in this order</option>
                      {order.items?.map((item) => (
                        <option key={item.id ?? item.product_id} value={item.id ? `item:${item.id}` : "order"}>
                          {itemLabel(item)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="rounded-xl border border-border/70 bg-surface-2/40 px-3 py-2 text-xs text-text-muted">
                  <span className="font-semibold text-text">Selected scope:</span> {returnScopeLabel}
                </div>
                <textarea
                  value={returnReason}
                  onChange={(e) => setReturnReason(e.target.value)}
                  placeholder={returnIntent === "replacement" ? "Describe what needs to be replaced..." : "Describe the reason for your return..."}
                  rows={3}
                  className="w-full rounded-xl border border-border bg-surface-2 text-text text-xs px-3 py-2 resize-none focus:outline-none focus:border-brand/60"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleReturn}
                    disabled={returning || !returnReason.trim()}
                    className="theme-btn-primary flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-bold disabled:opacity-50"
                  >
                    {returning ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
                    {returning ? "Submitting…" : returnIntent === "replacement" ? "Submit Replacement" : "Submit Return"}
                  </button>
                  <button
                    onClick={() => setShowReturnForm(false)}
                    className="px-4 py-2 rounded-xl border border-border text-text-muted text-xs hover:text-text transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowReturnForm(true)}
                className="theme-action-secondary flex w-full items-center justify-center gap-2 py-2 text-xs font-semibold"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Request a Return or Replacement
              </button>
            )}
          </motion.div>
        )}

        {/* Cancel section */}
        {canCancel && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="theme-card border rounded-2xl p-4"          >
            {cancelError && (
              <p className="theme-status-danger mb-2 text-xs">{cancelError}</p>            )}
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="theme-action-danger flex w-full items-center justify-center gap-2 py-2 text-xs font-semibold disabled:opacity-50"
            >
              {cancelling ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <XCircle className="w-3.5 h-3.5" />
              )}
              {cancelling ? "Cancelling…" : "Cancel Order"}
            </button>
          </motion.div>
        )}
      </div>
    </main>
  );
}
