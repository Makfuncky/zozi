"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Clock, Package, Truck, CheckCircle, ExternalLink, MapPin, Hash } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { buildTrackingSocketUrl, connectTrackingSocket, RealtimeStatus } from "@/lib/trackingRealtime";
import { useAuth } from "@/lib/useAuth";
import { OrderTracking } from "@/lib/types";
import { useCurrencyStore } from "@/lib/currencyStore";
import { buildTrackingMapHref, extractTrackingMapPoints } from "@shared/trackingMap";

interface PageProps {
  params: Promise<{ id: string }>;
}

function iconForStep(key: string) {
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
}

function liveStatusLabel(status: RealtimeStatus): string {
  switch (status) {
    case "connecting":
      return "Connecting to live updates...";
    case "live":
      return "Live updates connected";
    case "offline":
      return "Live updates unavailable";
    default:
      return "Waiting for live updates";
  }
}

function paymentMethodLabel(value?: string | null): string {
  if (!value) return "Not available";
  if (value === "cod") return "Cash on Delivery";
  if (value === "tap") return "Tap Payment";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function SharedTrackingPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const formatPrice = useCurrencyStore((state) => state.format);
  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [realtimeStatus, setRealtimeStatus] = useState<RealtimeStatus>("idle");
  const [responseNotes, setResponseNotes] = useState<Record<number, string>>({});
  const [responseError, setResponseError] = useState("");
  const [responseSuccess, setResponseSuccess] = useState("");
  const [submittingConfirmationId, setSubmittingConfirmationId] = useState<number | null>(null);
  const mapPoints = useMemo(() => extractTrackingMapPoints(tracking), [tracking]);
  const mapBounds = useMemo(() => {
    if (!mapPoints.length) return null;
    const latitudes = mapPoints.map((point) => point.latitude);
    const longitudes = mapPoints.map((point) => point.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    return {
      minLat,
      minLng,
      latSpan: Math.max(maxLat - minLat, 0.01),
      lngSpan: Math.max(maxLng - minLng, 0.01),
    };
  }, [mapPoints]);

  const loadTracking = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
      setError("");
    }
    const response = await apiFetch(`/orders/${id}/tracking`);
    if (!response.ok) {
      if (!silent) {
        const payload = await response.json().catch(() => null);
        setError(payload?.detail || "Could not load tracking details.");
        setTracking(null);
        setLoading(false);
      }
      return;
    }
    setTracking((await response.json()) as OrderTracking);
    if (!silent) {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.push("/login");
      return;
    }
    if (user?.role === "supplier") {
      router.replace(`/supplier/orders?order=${id}`);
      return;
    }
    loadTracking().catch(() => {
      setError("Could not load tracking details.");
      setLoading(false);
    });
  }, [authLoading, id, isLoggedIn, loadTracking, router, user?.role]);

  useEffect(() => {
    if (authLoading || !isLoggedIn || user?.role === "supplier") return;

    const socket = connectTrackingSocket(
      id,
      setRealtimeStatus,
      () => {
        void loadTracking({ silent: true });
      },
    );

    if (!socket) {
      return;
    }

    return () => {
      socket.close();
    };
  }, [authLoading, id, isLoggedIn, loadTracking, user?.role]);

  const handleConfirmationResponse = useCallback(async (orderId: number, confirmationId: number, decision: "accepted" | "rejected") => {
    setResponseError("");
    setResponseSuccess("");
    setSubmittingConfirmationId(confirmationId);
    try {
      const response = await apiFetch(`/orders/${orderId}/confirmation-requests/${confirmationId}/respond`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision,
          response_notes: responseNotes[confirmationId] || undefined,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setResponseError(payload?.detail || "Could not submit your response.");
        return;
      }
      setResponseSuccess(decision === "accepted" ? "Confirmation accepted." : "Confirmation rejected.");
      setResponseNotes((prev) => ({ ...prev, [confirmationId]: "" }));
      await loadTracking();
    } catch {
      setResponseError("Could not submit your response.");
    } finally {
      setSubmittingConfirmationId(null);
    }
  }, [loadTracking, responseNotes]);

  if (loading || authLoading) {
    return <main className="min-h-screen flex items-center justify-center text-text-muted">Loading tracker...</main>;
  }

  if (error || !tracking) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6">
        <div className="theme-card rounded-2xl border p-6 text-center">
          <p className="text-sm text-danger">{error || "Tracking not available."}</p>
          <button onClick={() => router.back()} className="mt-4 theme-link-brand text-sm">Go Back</button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="p-1.5 rounded-lg text-text-faint hover:text-text hover:bg-surface-2 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-text">Order Tracker #{tracking.order_id}</h1>
            <p className="text-xs text-text-faint">
              {tracking.delivered_shipments}/{tracking.shipment_count} shipments delivered
            </p>
            <p
              data-testid="tracking-live-status"
              className={`text-xs ${realtimeStatus === "live" ? "theme-status-success" : realtimeStatus === "connecting" ? "theme-status-info" : "text-text-faint"}`}
            >
              {liveStatusLabel(realtimeStatus)}
            </p>
          </div>
        </div>

        <div className="theme-card rounded-2xl border p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-text-faint">Order Status</p>
              <p className="mt-1 text-sm font-semibold text-text">{tracking.order_status.replaceAll("_", " ")}</p>
            </div>
            <div className="text-right text-xs text-text-muted">
              <p>Total: <span className="font-semibold text-text">{formatPrice(tracking.total_amount || 0)}</span></p>
              <p>Scan Codes: <span className="font-mono text-text">{tracking.available_scan_codes.join(", ") || "—"}</span></p>
            </div>
          </div>
          <div className="mt-4 flex items-start gap-0">
            {tracking.timeline.map((step, index) => {
              const StepIcon = iconForStep(step.key);
              const isLast = index === tracking.timeline.length - 1;
              return (
                <div key={step.key} className="flex items-center flex-1 min-w-0">
                  <div className="flex shrink-0 flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${step.completed ? "bg-success border-success" : step.active ? "bg-primary/20 border-primary" : "bg-surface-2 border-border"}`}>
                      <StepIcon className={`w-3.5 h-3.5 ${step.completed ? "text-on-brand" : step.active ? "theme-status-info" : "text-text-faint"}`} />
                    </div>
                    <span className={`mt-1 text-[10px] text-center whitespace-nowrap ${step.completed ? "theme-status-success" : step.active ? "theme-status-info font-semibold" : "text-text-faint"}`}>{step.label}</span>
                  </div>
                  {!isLast && <div className={`flex-1 h-0.5 mb-4 mx-1 ${step.completed ? "bg-success" : step.active ? "bg-primary/40" : "bg-border"}`} />}
                </div>
              );
            })}
          </div>
        </div>

        {responseError ? (
          <div className="theme-alert-danger rounded-2xl p-4 text-sm">{responseError}</div>
        ) : null}
        {responseSuccess ? (
          <div className="theme-alert-success rounded-2xl p-4 text-sm">{responseSuccess}</div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <div className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-bold text-text">Order Items</h2>
              <div className="mt-3 space-y-2">
                {tracking.items.map((item, index) => (
                  <div key={`${item.product_id}-${item.supplier_id ?? "x"}-${index}`} className="flex items-center justify-between rounded-xl border border-border/60 bg-surface-2/40 px-3 py-2 text-sm">
                    <div>
                      <p className="font-semibold text-text">{item.product_name}</p>
                      <p className="text-xs text-text-muted">Qty {item.quantity}{item.supplier_id ? ` · Supplier ${item.supplier_id}` : ""}</p>
                    </div>
                    <p className="font-semibold text-text">{formatPrice(item.price * item.quantity)}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-bold text-text">Shipment Journey</h2>
              <div className="mt-3 space-y-3">
                {tracking.shipments.map((shipment) => (
                  <div key={shipment.id} className="rounded-xl border border-border/60 bg-surface-2/40 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-text">Shipment #{shipment.id}{shipment.supplier_name ? ` · ${shipment.supplier_name}` : ""}</p>
                      <span className="rounded-lg bg-primary/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-primary">{shipment.status_label || shipment.status.replaceAll("_", " ")}</span>
                    </div>
                    <div className="mt-2 space-y-1 text-xs text-text-muted">
                      {shipment.current_hub ? <p>Current hub: <span className="text-text">{shipment.current_hub}</span></p> : null}
                      {shipment.distribution_channel ? <p>Channel: <span className="text-text">{shipment.distribution_channel.replaceAll("_", " ")}</span></p> : null}
                      {shipment.tracking_number ? <p>Tracking: <span className="font-mono text-text">{shipment.tracking_number}</span></p> : null}
                      {shipment.scan_code ? <p>Scan Code: <span className="font-mono text-text">{shipment.scan_code}</span></p> : null}
                      {shipment.package_count != null ? <p>Packages: <span className="text-text">{shipment.package_count}</span></p> : null}
                      {shipment.package_weight_kg != null ? <p>Weight: <span className="text-text">{shipment.package_weight_kg} kg</span></p> : null}
                      {shipment.package_dimensions ? <p>Dimensions: <span className="text-text">{shipment.package_dimensions}</span></p> : null}
                      {shipment.packaged_at ? <p>Packaged at: <span className="text-text">{new Date(shipment.packaged_at).toLocaleString()}</span></p> : null}
                      {shipment.packaging_notes ? <p>Packaging notes: <span className="text-text">{shipment.packaging_notes}</span></p> : null}
                      {shipment.estimated_delivery ? <p>ETA: <span className="text-text">{new Date(shipment.estimated_delivery).toLocaleString()}</span></p> : null}
                      {shipment.delivery_signature_name ? <p>Received by: <span className="text-text">{shipment.delivery_signature_name}</span></p> : null}
                      {shipment.delivery_signature_captured_at ? <p>Signature captured: <span className="text-text">{new Date(shipment.delivery_signature_captured_at).toLocaleString()}</span></p> : null}
                      {shipment.tracking_url ? <Link href={shipment.tracking_url} target="_blank" className="theme-link-brand">Open carrier tracking</Link> : null}
                    </div>
                    {shipment.active_confirmation_request ? (
                      <div className="mt-3 rounded-xl border border-border/50 bg-surface-1/60 p-3 text-xs text-text-muted">
                        <p className="font-bold uppercase tracking-wide text-text-faint">Pending Confirmation</p>
                        <p className="mt-2 text-sm font-semibold text-text">
                          {shipment.active_confirmation_request.confirmation_type_label || shipment.active_confirmation_request.confirmation_type.replaceAll("_", " ")}
                        </p>
                        <p>
                          Requested status: <span className="text-text">{shipment.active_confirmation_request.requested_status.replaceAll("_", " ")}</span>
                        </p>
                        <p>
                          Awaiting: <span className="text-text">{shipment.active_confirmation_request.target_role || "recipient"}</span>
                        </p>
                        {shipment.active_confirmation_request.current_hub ? <p>Hub: <span className="text-text">{shipment.active_confirmation_request.current_hub}</span></p> : null}
                        {shipment.active_confirmation_request.tracking_number ? <p>Tracking: <span className="font-mono text-text">{shipment.active_confirmation_request.tracking_number}</span></p> : null}
                        {shipment.active_confirmation_request.notes ? <p>Request note: <span className="text-text">{shipment.active_confirmation_request.notes}</span></p> : null}
                        {shipment.active_confirmation_request.created_at ? <p>Requested: <span className="text-text">{new Date(shipment.active_confirmation_request.created_at).toLocaleString()}</span></p> : null}
                        {(user?.id === shipment.active_confirmation_request.target_user_id || user?.role === "admin" || user?.role === "sub_admin") ? (
                          <div className="mt-3 space-y-2">
                            <textarea
                              value={responseNotes[shipment.active_confirmation_request.id] || ""}
                              onChange={(event) => setResponseNotes((prev) => ({ ...prev, [shipment.active_confirmation_request!.id]: event.target.value }))}
                              placeholder="Optional response note"
                              className="theme-input min-h-24 w-full rounded-xl border px-3 py-2 text-sm"
                            />
                            <div className="flex flex-wrap gap-2">
                              <button
                                onClick={() => void handleConfirmationResponse(tracking.order_id, shipment.active_confirmation_request!.id, "accepted")}
                                disabled={submittingConfirmationId === shipment.active_confirmation_request.id}
                                className="theme-btn-primary rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-50"
                              >
                                Accept Confirmation
                              </button>
                              <button
                                onClick={() => void handleConfirmationResponse(tracking.order_id, shipment.active_confirmation_request!.id, "rejected")}
                                disabled={submittingConfirmationId === shipment.active_confirmation_request.id}
                                className="theme-btn-secondary rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-50"
                              >
                                Reject Confirmation
                              </button>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                    {shipment.delivery_signature_data_url ? (
                      <div className="mt-3 rounded-xl border border-border/50 bg-white p-3">
                        <p className="text-[11px] font-bold uppercase tracking-wide text-text-faint">Delivery Signature</p>
                        <img src={shipment.delivery_signature_data_url} alt={`Delivery signature for shipment ${shipment.id}`} className="mt-2 max-h-32 rounded-lg border border-border bg-white" />
                      </div>
                    ) : null}
                    {shipment.events?.length ? (
                      <div className="mt-3 rounded-xl border border-border/50 bg-surface-1/60 p-3">
                        <p className="text-[11px] font-bold uppercase tracking-wide text-text-faint">Event Trail</p>
                        <div className="mt-2 space-y-2">
                          {shipment.events.map((event) => (
                            <div key={event.id} className="border-l-2 border-primary/30 pl-3 text-xs text-text-muted">
                              <p className="font-semibold text-text">{event.event_label || event.event_type.replaceAll("_", " ")}</p>
                              <p>
                                {event.created_at ? new Date(event.created_at).toLocaleString() : "Pending timestamp"}
                                {event.actor_role ? ` · ${event.actor_role}` : ""}
                              </p>
                              {event.location ? <p>Location: <span className="text-text">{event.location}</span></p> : null}
                              {event.notes ? <p>{event.notes}</p> : null}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-bold text-text">Live Route Map</h2>
              {mapPoints.length && mapBounds ? (
                <>
                  <div className="relative mt-3 h-52 overflow-hidden rounded-2xl border border-border bg-linear-to-br from-sky-100 via-cyan-50 to-white">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.18),transparent_55%)]" />
                    {mapPoints.map((point) => {
                      const left = 8 + ((point.longitude - mapBounds.minLng) / mapBounds.lngSpan) * 84;
                      const top = 8 + (1 - (point.latitude - mapBounds.minLat) / mapBounds.latSpan) * 78;
                      return (
                        <div
                          key={point.shipmentId}
                          className="absolute flex h-5 w-5 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-white bg-primary shadow-lg"
                          style={{ left: `${left}%`, top: `${top}%` }}
                          title={point.label}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-white" />
                        </div>
                      );
                    })}
                    <div className="absolute inset-x-3 bottom-3 rounded-xl bg-surface-base/90 px-3 py-2 text-xs text-text-muted shadow-lg backdrop-blur">
                      Latest GPS checkpoints from shipment events. Open a checkpoint below to jump into OpenStreetMap.
                    </div>
                  </div>
                  <div className="mt-3 space-y-2">
                    {mapPoints.map((point) => (
                      <a
                        key={point.shipmentId}
                        href={buildTrackingMapHref(point.latitude, point.longitude)}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center justify-between rounded-xl border border-border/60 bg-surface-2/40 px-3 py-2 text-sm transition-colors hover:border-primary/40"
                      >
                        <div>
                          <p className="font-semibold text-text">{point.label}</p>
                          <p className="text-xs text-text-muted">
                            {point.location || point.currentHub || "Latest GPS checkpoint"}
                            {point.recordedAt ? ` · ${new Date(point.recordedAt).toLocaleString()}` : ""}
                          </p>
                        </div>
                        <ExternalLink className="h-4 w-4 text-text-faint" />
                      </a>
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-3 text-xs text-text-muted">No GPS checkpoints have been published for this order yet.</p>
              )}
            </div>

            <div className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-bold text-text">Delivery Details</h2>
              <div className="mt-3 space-y-2 text-xs text-text-muted">
                {tracking.shipping_address ? <div className="flex items-start gap-2"><MapPin className="mt-0.5 h-3.5 w-3.5 theme-status-info shrink-0" /><span>{tracking.shipping_address}</span></div> : null}
                {tracking.delivery_location ? <p>Location: <span className="text-text">{tracking.delivery_location}</span></p> : null}
                {tracking.customer_phone ? <p>Phone: <span className="text-text">{tracking.customer_phone}</span></p> : null}
                {tracking.delivery_note ? <p>Note: <span className="text-text">{tracking.delivery_note}</span></p> : null}
              </div>
            </div>

            {tracking.active_return_request ? (
              <div className="theme-card rounded-2xl border p-4">
                <h2 className="text-sm font-bold text-text">Return / Replacement</h2>
                <div className="mt-3 space-y-2 text-xs text-text-muted">
                  <p>
                    Intent: <span className="font-semibold text-text capitalize">{tracking.active_return_request.intent}</span>
                  </p>
                  <p>
                    Status: <span className="font-semibold text-text capitalize">{tracking.active_return_request.status.replaceAll("_", " ")}</span>
                  </p>
                  <p>
                    Reason: <span className="text-text">{tracking.active_return_request.reason}</span>
                  </p>
                  {tracking.active_return_request.resolution_notes ? (
                    <p>
                      Resolution: <span className="text-text">{tracking.active_return_request.resolution_notes}</span>
                    </p>
                  ) : null}
                  {tracking.active_return_request.updated_at ? (
                    <p>
                      Last updated: <span className="text-text">{new Date(tracking.active_return_request.updated_at).toLocaleString()}</span>
                    </p>
                  ) : null}
                </div>
              </div>
            ) : null}

            <div className="theme-card rounded-2xl border p-4">
              <h2 className="text-sm font-bold text-text">Finance Breakdown</h2>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between text-text-muted"><span>Payment Method</span><span>{paymentMethodLabel(tracking.finance_breakdown?.payment_method || tracking.payment_method)}</span></div>
                <div className="flex justify-between text-text-muted"><span>Subtotal</span><span>{formatPrice(tracking.subtotal_amount || 0)}</span></div>
                <div className="flex justify-between text-text-muted"><span>Discount</span><span>{formatPrice(tracking.discount_amount || 0)}</span></div>
                <div className="flex justify-between text-text-muted"><span>VAT</span><span>{formatPrice(tracking.vat_amount || 0)}</span></div>
                <div className="flex justify-between text-text-muted"><span>Shipping</span><span>{formatPrice(tracking.shipping_amount || 0)}</span></div>
                <div className="flex justify-between text-text-muted"><span>Service Fee</span><span>{formatPrice(tracking.finance_breakdown?.service_fee_amount || 0)}</span></div>
                <div className="flex justify-between font-bold text-text"><span>Total</span><span>{formatPrice(tracking.total_amount || 0)}</span></div>
              </div>
              {tracking.finance_breakdown?.allocations?.length ? (
                <div className="mt-4 space-y-2 border-t border-border pt-3">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-text-faint">Delivery Allocation Snapshot</p>
                  {tracking.finance_breakdown.allocations.map((allocation) => (
                    <div key={`${allocation.supplier_id}-${allocation.partner_id ?? "na"}`} className="rounded-xl border border-border/60 bg-surface-2/40 p-3 text-xs text-text-muted">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-text">{allocation.supplier_name || `Supplier #${allocation.supplier_id}`}</p>
                        <p className="font-semibold text-text">{formatPrice(allocation.shipping_amount)}</p>
                      </div>
                      <p className="mt-1">
                        {allocation.partner_name || "Fallback shipping"}
                        {allocation.destination_city || allocation.destination_country ? ` · ${allocation.destination_city || ""}${allocation.destination_city && allocation.destination_country ? ", " : ""}${allocation.destination_country || ""}` : ""}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                        <span>Pickup: <span className="text-text">{formatPrice(allocation.pickup_charge)}</span></span>
                        <span>Drop-off: <span className="text-text">{formatPrice(allocation.dropoff_charge)}</span></span>
                        {allocation.estimated_delivery_min != null || allocation.estimated_delivery_max != null ? (
                          <span>
                            ETA: <span className="text-text">{allocation.estimated_delivery_min ?? allocation.estimated_delivery_max}-{allocation.estimated_delivery_max ?? allocation.estimated_delivery_min} days</span>
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
              {tracking.finance_breakdown?.refund ? (
                <div className="mt-4 space-y-2 border-t border-border pt-3 text-xs text-text-muted">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-text-faint">Refund Impact</p>
                  <div className="flex justify-between"><span>Status</span><span className="text-text capitalize">{tracking.finance_breakdown.refund.status.replaceAll("_", " ")}</span></div>
                  <div className="flex justify-between"><span>Customer Refund</span><span className="text-text">{formatPrice(tracking.finance_breakdown.refund.customer_refund_amount)}</span></div>
                  <div className="flex justify-between"><span>VAT Adjustment</span><span className="text-text">{formatPrice(tracking.finance_breakdown.refund.vat_adjustment)}</span></div>
                </div>
              ) : null}
            </div>

            {tracking.tracking_numbers.length ? (
              <div className="theme-card rounded-2xl border p-4">
                <h2 className="text-sm font-bold text-text">Tracking Numbers</h2>
                <div className="mt-3 space-y-2">
                  {tracking.tracking_numbers.map((trackingNumber) => (
                    <div key={trackingNumber} className="flex items-center gap-2 text-xs text-text-muted">
                      <Hash className="h-3.5 w-3.5 theme-status-info shrink-0" />
                      <span className="font-mono text-text">{trackingNumber}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
