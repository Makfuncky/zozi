"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { RefreshCw, Truck, ScanLine, Map as MapIcon, Camera, X } from "@/lib/icons";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { getStatusChip } from "@shared/statusColors";
import ParcelTracker from "@/components/country/ParcelTracker";

const MapView = dynamic(() => import("@/components/map/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[200px] items-center justify-center rounded-xl border border-border bg-surface-2 text-xs text-text-faint">
      Loading map…
    </div>
  ),
});

interface PricingBreakdown {
  shipping_amount?: number;
  pickup_fee?: number;
  dropoff_fee?: number;
  ceiling_applied?: boolean;
}

interface Shipment {
  id: number;
  order_id: number;
  tracking_number?: string | null;
  scan_code?: string | null;
  carrier_name?: string | null;
  status: string;
  current_hub?: string | null;
  shipping_address?: string | null;
  delivery_location?: string | null;
  estimated_delivery?: string | null;
  accepted_load_fit_label?: string | null;
  accepted_load_fit_factor?: number | null;
  accepted_shipping_amount?: number | null;
  accepted_vehicle_selected_at?: string | null;
  estimated_partner_payout?: number | null;
  pricing_breakdown?: PricingBreakdown | null;
  active_confirmation_request?: {
    id: number;
    confirmation_type: string;
    status: string;
    requested_status: string;
    requested_event_type: string;
  } | null;
}

const PAGE = 1;
const PAGE_SIZE = 30;

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "prepared", label: "Prepared" },
  { value: "picking_up", label: "Picking Up" },
  { value: "shipped", label: "Shipped" },
  { value: "in_transit", label: "In Transit" },
  { value: "delivered", label: "Delivered" },
  { value: "failed", label: "Failed" },
  { value: "returned", label: "Returned" },
];

interface StatusAction {
  status: string;
  event: string;
  label: string;
  requireScan?: boolean;
  deliver?: boolean;
  terminalStatus?: string;
  danger?: boolean;
  requestPickup?: boolean;
}

function getActions(status: string): StatusAction[] {
  switch (status) {
    case "prepared":
      return [{ status: "picking_up", event: "pickup_confirmed", label: "Confirm Pickup" }];
    case "picking_up":
      return [
        { status: "shipped", event: "picked_from_supplier", label: "Scan Picked From Supplier", requireScan: true },
        { status: "picking_up", event: "pickup_request", label: "Request Pickup Confirmation", requestPickup: true },
        { status: "picking_up", event: "logistics_received", label: "Logistics Received" },
        { status: "picking_up", event: "shipment_delayed", label: "Mark Delayed" },
        { status: "picking_up", event: "shipment_rescheduled", label: "Mark Rescheduled" },
        { status: "picking_up", event: "shipment_cancelled", label: "Mark Cancelled (return to supplier)", terminalStatus: "returned", danger: true },
        { status: "failed", event: "shipment_failed", label: "Mark Failed", terminalStatus: "failed", danger: true },
        { status: "returned", event: "shipment_returned", label: "Mark Returned", terminalStatus: "returned", danger: true },
      ];
    case "shipped":
      return [
        { status: "in_transit", event: "out_for_delivery", label: "Out for Delivery" },
        { status: "shipped", event: "distribution_checkpoint", label: "Distribution Checkpoint" },
        { status: "shipped", event: "logistics_received", label: "Logistics Received" },
        { status: "shipped", event: "shipment_delayed", label: "Mark Delayed" },
        { status: "shipped", event: "shipment_rescheduled", label: "Mark Rescheduled" },
        { status: "shipped", event: "shipment_cancelled", label: "Mark Cancelled (return to supplier)", terminalStatus: "returned", danger: true },
        { status: "failed", event: "shipment_failed", label: "Mark Failed", terminalStatus: "failed", danger: true },
        { status: "returned", event: "shipment_returned", label: "Mark Returned", terminalStatus: "returned", danger: true },
      ];
    case "in_transit":
      return [
        { status: "in_transit", event: "distribution_checkpoint", label: "Distribution Checkpoint" },
        { status: "in_transit", event: "out_for_delivery", label: "Out for Delivery" },
        { status: "in_transit", event: "shipment_delayed", label: "Mark Delayed" },
        { status: "in_transit", event: "shipment_rescheduled", label: "Mark Rescheduled" },
        { status: "in_transit", event: "shipment_cancelled", label: "Mark Cancelled (return to supplier)", terminalStatus: "returned", danger: true },
        { status: "delivered", event: "customer_received", label: "Deliver (e-sign)", deliver: true },
        { status: "failed", event: "shipment_failed", label: "Mark Failed", terminalStatus: "failed", danger: true },
        { status: "returned", event: "shipment_returned", label: "Mark Returned", terminalStatus: "returned", danger: true },
      ];
    default:
      return [];
  }
}

function cap(text?: string | null) {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function statusStyle(status?: string | null): string {
  return getStatusChip(status);
}

/* ---------------- QR Scan Modal ---------------- */
function ScanModal({
  open,
  onClose,
  onScanned,
}: {
  open: boolean;
  onClose: () => void;
  onScanned: (code: string) => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const readerRef = useRef<any>(null);
  const [manual, setManual] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let stream: MediaStream | null = null;

    async function startCamera() {
      try {
        if (!navigator.mediaDevices?.getUserMedia) throw new Error("Camera API unavailable");
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        if (cancelled || !videoRef.current) return;
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
        const { BrowserMultiFormatReader } = await import("@zxing/library");
        const reader = new BrowserMultiFormatReader();
        readerRef.current = reader;
        (reader as any).decodeFromVideoElement(videoRef.current, (result: any) => {
          if (result && result.getText && !cancelled) {
            const code = result.getText();
            if (code) onScanned(code);
          }
        });
      } catch (e: any) {
        setErr(e?.message || "Camera unavailable — use manual entry");
      }
    }
    void startCamera();

    return () => {
      cancelled = true;
      try {
        readerRef.current?.reset?.();
      } catch {}
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [open, onScanned]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose} role="dialog" aria-modal="true">
        <div
          className="theme-modal-card w-full max-w-md p-4"
          onClick={(e) => e.stopPropagation()}
        >
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-bold text-text">Scan Order QR</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-text-muted hover:text-text" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <video ref={videoRef} className="aspect-square w-full rounded-xl bg-black" muted playsInline />
        {err ? <p className="mt-2 text-xs text-warning">{err}</p> : null}
        <div className="mt-3 flex items-center gap-2">
          <input
            value={manual}
            onChange={(e) => setManual(e.target.value)}
            placeholder="Or enter scan code manually"
            className="h-9 flex-1 rounded-xl border border-border bg-surface-1 px-3 text-xs text-text focus:border-primary focus:outline-none"
          />
          <button
            onClick={() => manual.trim() && onScanned(manual.trim())}
            className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold"
          >
            Use
          </button>
        </div>
      </div>
    </div>
  );
}

export default function LogisticsPartnerShipmentsPage() {
  const router = useRouter();
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [mapShipmentId, setMapShipmentId] = useState<number | null>(null);
  const [trackShipmentId, setTrackShipmentId] = useState<number | null>(null);
  const [actionShipmentId, setActionShipmentId] = useState<number | null>(null);
  const [scanShipmentId, setScanShipmentId] = useState<number | null>(null);
  const [notesByShipment, setNotesByShipment] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);

  const fetchShipments = useCallback(async (status?: string) => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ page: String(PAGE), page_size: String(PAGE_SIZE) });
      if (status) qs.set("status", status);
      const res = await apiFetch(`/logistics-partner/shipments?${qs.toString()}`);
      if (!res.ok) throw new Error(`Failed to load shipments (${res.status})`);
      const data = await res.json();
      const items: Shipment[] = Array.isArray(data) ? data : (data?.items ?? []);
      setShipments(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shipments");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchShipments();
  }, [fetchShipments]);

  function toggleSelect(id: number) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function updateStatus(shipment: Shipment, action: StatusAction, scanCode?: string) {
    if (action.deliver) {
      router.push(`/logistics-partner/scan?code=${shipment.scan_code || shipment.tracking_number || shipment.id}`);
      return;
    }
    setBusyId(shipment.id);
    try {
      const payload: Record<string, any> = {
        status: action.terminalStatus || action.status,
        event_type: action.event,
        notes: notesByShipment[shipment.id] || "",
      };
      if (scanCode) payload.scan_code = scanCode;
      if (action.status === "in_transit" && action.event === "out_for_delivery") {
        payload.current_hub = shipment.current_hub || "Distribution Center";
      }
      const res = await apiFetch(`/logistics-partner/shipments/${shipment.id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const updated = await res.json().catch(() => null);
        setShipments((prev) =>
          prev.map((s) => (s.id === shipment.id ? { ...s, ...(updated ?? {}), status: updated?.status ?? payload.status } : s)),
        );
        setActionShipmentId(null);
        setNotesByShipment((prev) => ({ ...prev, [shipment.id]: "" }));
      } else {
        const j = await res.json().catch(() => ({}));
        setError(j.detail || `Failed to update shipment ${shipment.id}`);
      }
    } catch {
      setError("Network error updating shipment");
    } finally {
      setBusyId(null);
    }
  }

  async function requestPickupConfirmation(shipment: Shipment) {
    setBusyId(shipment.id);
    try {
      const res = await apiFetch(`/logistics-partner/shipments/${shipment.id}/confirmation-request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requested_status: "shipped",
          event_type: "picked_from_supplier",
          notes: "Logistics partner requests supplier confirmation for pickup",
        }),
      });
      if (res.ok) {
        const updated = await res.json().catch(() => null);
        setShipments((prev) =>
          prev.map((s) =>
            s.id === shipment.id
              ? { ...s, active_confirmation_request: updated?.request ?? s.active_confirmation_request }
              : s,
          ),
        );
        setActionShipmentId(null);
      } else {
        const j = await res.json().catch(() => ({}));
        setError(j.detail || `Failed to request pickup confirmation for shipment ${shipment.id}`);
      }
    } catch {
      setError("Network error requesting pickup confirmation");
    } finally {
      setBusyId(null);
    }
  }

  async function applyBulkStatus(nextStatus: string) {
    if (selectedIds.length === 0) return;
    try {
      const res = await apiFetch(`/logistics-partner/shipments/bulk-status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shipment_ids: selectedIds, status: nextStatus }),
      });
      if (res.ok) {
        setShipments((prev) =>
          prev.map((s) => (selectedIds.includes(s.id) ? { ...s, status: nextStatus } : s)),
        );
        setSelectedIds([]);
        fetchShipments(statusFilter || undefined);
      }
    } catch {
      // silent
    }
  }

  function onScanned(code: string) {
    const id = scanShipmentId;
    setScanShipmentId(null);
    if (id == null) return;
    const shipment = shipments.find((s) => s.id === id);
    if (!shipment) return;
    updateStatus(shipment, { status: "shipped", event: "picked_from_supplier", label: "Scan Picked From Supplier", requireScan: true }, code);
  }

  const selectedCount = selectedIds.length;

  return (
    <LogisticsPartnerLayout title="Shipments">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-text">Shipments</h1>
            <p className="text-xs text-text-muted">Pickups, scanning, route updates and tracking</p>
          </div>
          <div className="flex items-center gap-2">
            <select
              aria-label="Filter by status"
              value={statusFilter}
              onChange={(e) => {
                const value = e.target.value;
                setStatusFilter(value);
                fetchShipments(value || undefined);
              }}
              className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => fetchShipments(statusFilter || undefined)}
              disabled={loading}
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">{error}</div>
        )}

        {selectedCount > 0 && (
          <div
            data-testid="bulk-action-bar"
            className="flex items-center justify-between rounded-xl border border-border bg-surface-2 px-3 py-2"
          >
            <span className="text-xs font-semibold text-text">{selectedCount} selected</span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => applyBulkStatus("in_transit")}
                className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold"
              >
                Set to in_transit
              </button>
              <button
                type="button"
                onClick={() => applyBulkStatus("delivered")}
                className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold"
              >
                Set to delivered
              </button>
            </div>
          </div>
        )}

        <div className="rounded-xl border">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-2 py-2 text-left">Select</th>
                  <th className="px-2 py-2 text-left">Order</th>
                  <th className="px-2 py-2 text-left">Tracking</th>
                  <th className="px-2 py-2 text-left">Carrier</th>
                  <th className="px-2 py-2 text-left">Status</th>
                  <th className="px-2 py-2 text-left">Hub</th>
                  <th className="px-2 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {shipments.map((s) => {
                  const actions = getActions(s.status);
                  return (
                    <React.Fragment key={s.id}>
                      <tr className="border-t">
                        <td className="px-2 py-2">
                          <input
                            type="checkbox"
                            aria-label="Select row"
                            checked={selectedIds.includes(s.id)}
                            onChange={() => toggleSelect(s.id)}
                          />
                        </td>
                        <td className="px-2 py-2 text-text">
                          #{s.order_id}
                          <div className="font-mono text-[10px] text-text-faint">{s.scan_code || "—"}</div>
                        </td>
                        <td className="px-2 py-2 font-mono text-text-muted">{s.tracking_number || "—"}</td>
                        <td className="px-2 py-2 text-text-muted">{s.carrier_name || "—"}</td>
                        <td className="px-2 py-2">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${statusStyle(s.status)}`}>
                            {s.status}
                          </span>
                          {s.accepted_load_fit_label ? (
                            <span className="ml-2 text-[11px] text-text-muted">
                              Load-fit lock: {cap(s.accepted_load_fit_label)} x
                              {(Number(s.accepted_load_fit_factor) || 0).toFixed(2)}
                            </span>
                          ) : null}
                          {s.active_confirmation_request?.confirmation_type === "pickup" &&
                          s.active_confirmation_request.status === "pending" ? (
                            <span className="ml-2 rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-medium text-warning">
                              Awaiting supplier pickup confirm
                            </span>
                          ) : null}
                        </td>
                        <td className="px-2 py-2 text-text-faint">{s.current_hub || "—"}</td>
                        <td className="px-2 py-2">
                          <div className="flex flex-wrap items-center gap-1">
                            {s.delivery_location && (
                              <button
                                type="button"
                                onClick={() => setMapShipmentId((prev) => (prev === s.id ? null : s.id))}
                                className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold"
                              >
                                <MapIcon className="mr-1 inline h-3.5 w-3.5" />
                                {mapShipmentId === s.id ? "Hide" : "Map"}
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setTrackShipmentId((prev) => (prev === s.id ? null : s.id))}
                              className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold"
                            >
                              Track
                            </button>

                            {s.status === "prepared" ? (
                              <button
                                type="button"
                                onClick={() => updateStatus(s, { status: "picking_up", event: "pickup_confirmed", label: "Confirm Pickup" })}
                                disabled={busyId === s.id}
                                className="theme-btn-primary rounded-lg px-2 py-1 text-xs font-semibold disabled:opacity-50"
                              >
                                Confirm Pickup
                              </button>
                            ) : null}

                            {actions.length > 0 ? (
                              <button
                                type="button"
                                onClick={() => setActionShipmentId((prev) => (prev === s.id ? null : s.id))}
                                className="theme-btn-primary rounded-lg px-2 py-1 text-xs font-semibold"
                              >
                                Update Status
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>

                      {mapShipmentId === s.id && s.delivery_location && (
                        <tr key={`${s.id}-map`}>
                          <td colSpan={7} className="px-2 pb-2">
                            <MapView location={s.delivery_location} height="220px" markerLabel={`Order #${s.order_id}`} markerColor="#3b82f6" />
                          </td>
                        </tr>
                      )}

                      {trackShipmentId === s.id && (
                        <tr key={`${s.id}-track`}>
                          <td colSpan={7} className="px-2 pb-2">
                            <ParcelTracker parcelId={String(s.order_id)} />
                          </td>
                        </tr>
                      )}

                      {actionShipmentId === s.id && (
                        <tr key={`${s.id}-action`}>
                          <td colSpan={7} className="px-2 pb-3">
                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                                Update Shipment #{s.id}
                              </p>
                                <div className="flex flex-wrap gap-2">
                                  {actions.map((a) => (
                                    <button
                                      key={a.event}
                                      type="button"
                                      disabled={busyId === s.id}
                                      onClick={() => {
                                        if (a.requireScan) {
                                          setScanShipmentId(s.id);
                                        } else if (a.requestPickup) {
                                          void requestPickupConfirmation(s);
                                        } else {
                                          void updateStatus(s, a);
                                        }
                                      }}
                                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50 ${
                                        a.requireScan || a.requestPickup
                                          ? "theme-btn-primary"
                                          : a.danger
                                            ? "bg-danger/10 text-danger hover:bg-danger/20"
                                            : "theme-btn-secondary"
                                      }`}
                                    >
                                      {a.requireScan ? <ScanLine className="mr-1 inline h-3.5 w-3.5" /> : null}
                                      {a.label}
                                    </button>
                                  ))}
                                </div>
                                {s.active_confirmation_request?.confirmation_type === "pickup" &&
                                s.active_confirmation_request.status === "pending" ? (
                                  <p className="mt-2 rounded-lg bg-warning/10 px-2 py-1 text-[11px] font-medium text-warning">
                                    Awaiting supplier pickup confirmation — order will become “Picked From Supplier” once the
                                    supplier accepts.
                                  </p>
                                ) : null}
                              <div className="mt-3 flex items-center gap-2">
                                <input
                                  value={notesByShipment[s.id] || ""}
                                  onChange={(e) => setNotesByShipment((prev) => ({ ...prev, [s.id]: e.target.value }))}
                                  placeholder="Optional status note (e.g. delay reason, hub)"
                                  className="h-9 flex-1 rounded-xl border border-border bg-surface px-3 text-xs text-text focus:border-primary focus:outline-none"
                                />
                                <button
                                  type="button"
                                  onClick={() => setActionShipmentId(null)}
                                  className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text-muted"
                                >
                                  Close
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {!loading && shipments.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <Truck className="h-8 w-8 text-text-faint" />
              <p className="text-sm text-text-muted">No shipments match this filter.</p>
            </div>
          ) : null}
        </div>
      </PanelContent>

      <ScanModal open={scanShipmentId != null} onClose={() => setScanShipmentId(null)} onScanned={onScanned} />
    </LogisticsPartnerLayout>
  );
}
