"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useState } from "react";
import { MapPin, Navigation, Clock, Package, Truck, ExternalLink, RefreshCw } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import type { OrderTracking, OrderTrackingShipment } from "@/lib/types";

interface ParcelTrackerProps {
  parcelId: string;
  isAdminView?: boolean;
}

const STATUS_STYLES: Record<string, string> = {
  delivered: "bg-success/10 text-success",
  in_transit: "bg-primary/10 text-primary",
  shipped: "bg-primary/10 text-primary",
  picking_up: "bg-primary/10 text-primary",
  prepared: "bg-warning/10 text-warning",
  processing: "bg-warning/10 text-warning",
  cancelled: "bg-danger/10 text-danger",
  failed: "bg-danger/10 text-danger",
};

function statusStyle(status?: string | null): string {
  if (!status) return "bg-surface-2 text-text-muted";
  return STATUS_STYLES[status] ?? "bg-surface-2 text-text-muted";
}

export default function ParcelTracker({ parcelId, isAdminView = false }: ParcelTrackerProps) {
  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchTracking = useCallback(async () => {
    if (!parcelId) return;
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch(`/orders/${parcelId}/tracking`);
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(payload?.detail || "Tracking details are not available for this reference.");
        setTracking(null);
        return;
      }
      setTracking((await response.json()) as OrderTracking);
    } catch {
      setError("Could not reach the tracking service.");
      setTracking(null);
    } finally {
      setLoading(false);
    }
  }, [parcelId]);

  useEffect(() => {
    void fetchTracking();
  }, [fetchTracking]);

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent mx-auto mb-2" />
        <p className="text-sm text-text-muted">Looking up parcel...</p>
      </div>
    );
  }

  if (error || !tracking) {
    return (
      <div className="text-center py-8">
        <Package className="h-12 w-12 text-text-muted mx-auto mb-3" />
        <p className="text-sm text-text-muted mb-3">{error || "Enter a tracking reference to view status"}</p>
        <Button variant="primary" className="inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs transition" onClick={() => void fetchTracking()}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Track Parcel
        </Button>
      </div>
    );
  }

  const primaryShipment: OrderTrackingShipment | undefined = tracking.shipments?.[0];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-text">Order #{tracking.order_id}</h3>
          <p className="text-xs text-text-muted">
            {tracking.delivered_shipments}/{tracking.shipment_count} shipments delivered
          </p>
        </div>
        <span className={`px-2 py-1 rounded text-[10px] font-semibold uppercase ${statusStyle(tracking.order_status)}`}>
          {tracking.order_status_label || tracking.order_status?.replaceAll("_", " ")}
        </span>
      </div>

      <div className="border border-border rounded-lg p-3 bg-surface-1">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-text-muted">Status</span>
            <p className="font-medium text-text">{tracking.order_status_label || tracking.order_status}</p>
          </div>
          <div>
            <span className="text-text-muted">Scan Codes</span>
            <p className="font-mono font-medium text-text">{tracking.available_scan_codes.join(", ") || "—"}</p>
          </div>
          <div>
            <span className="text-text-muted">Tracking #</span>
            <p className="font-mono font-medium text-text">{tracking.tracking_numbers[0] || "Pending"}</p>
          </div>
          <div>
            <span className="text-text-muted">Shipments</span>
            <p className="font-medium text-text">{tracking.shipment_count}</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {tracking.shipments.map((shipment) => (
          <div key={shipment.id} className="rounded-xl border border-border/60 bg-surface-2/40 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-text">
                Shipment #{shipment.id}{shipment.supplier_name ? ` · ${shipment.supplier_name}` : ""}
              </p>
              <span className={`rounded-lg px-2 py-1 text-[10px] font-semibold uppercase ${statusStyle(shipment.status)}`}>
                {shipment.status_label || shipment.status?.replaceAll("_", " ")}
              </span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-text-muted">
              {shipment.current_hub ? (
                <p className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {shipment.current_hub}</p>
              ) : null}
              {shipment.distribution_channel ? (
                <p className="flex items-center gap-1"><Navigation className="h-3 w-3" /> {shipment.distribution_channel.replaceAll("_", " ")}</p>
              ) : null}
              {shipment.tracking_number ? (
                <p className="flex items-center gap-1"><Truck className="h-3 w-3" /> <span className="font-mono">{shipment.tracking_number}</span></p>
              ) : null}
              {shipment.scan_code ? (
                <p className="flex items-center gap-1"><Package className="h-3 w-3" /> <span className="font-mono">{shipment.scan_code}</span></p>
              ) : null}
              {shipment.estimated_delivery ? (
                <p className="flex items-center gap-1"><Clock className="h-3 w-3" /> ETA {new Date(shipment.estimated_delivery).toLocaleString()}</p>
              ) : null}
            </div>
            {shipment.tracking_url ? (
              <a href={shipment.tracking_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs text-primary hover:underline">
                <ExternalLink className="h-3 w-3" /> Open carrier tracking
              </a>
            ) : null}
          </div>
        ))}
      </div>

      {isAdminView && (
        <a href={`/tracking/${tracking.order_id}`} className="text-xs text-primary hover:underline flex items-center gap-1">
          <ExternalLink className="h-3 w-3" />
          View in full tracking dashboard
        </a>
      )}
    </div>
  );
}
