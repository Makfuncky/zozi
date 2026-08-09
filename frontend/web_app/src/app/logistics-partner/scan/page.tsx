"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ScanLine, Truck } from "@/lib/icons";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import SignaturePad from "@/components/SignaturePad";

interface Shipment {
  id: number;
  order_id: number;
  status: string;
  status_label?: string;
  tracking_number?: string | null;
  scan_code?: string | null;
  current_hub?: string | null;
  shipping_address?: string | null;
  customer_name?: string | null;
  customer_phone?: string | null;
}

function LogisticsPartnerScanInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCode = searchParams?.get("code") ?? "";

  const [codeInput, setCodeInput] = useState(initialCode);
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requestedStatus, setRequestedStatus] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [signature, setSignature] = useState<string | null>(null);
  const [resultMsg, setResultMsg] = useState<string | null>(null);

  const lookup = useCallback(async (code: string) => {
    if (!code) return;
    setLoading(true);
    setError(null);
    setShipment(null);
    try {
      const res = await apiFetch(`/logistics-partner/shipments/scan?code=${encodeURIComponent(code)}`);
      if (!res.ok) throw new Error(`Shipment not found (${res.status})`);
      setShipment(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Shipment not found");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialCode) lookup(initialCode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function sendConfirmationRequest() {
    if (!shipment) return;
    if (!customerName || !signature) {
      setError("Customer name and signature are required to confirm delivery.");
      return;
    }
    setError(null);
    try {
      const res = await apiFetch(`/logistics-partner/shipments/${shipment.id}/confirmation-request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requested_status: requestedStatus || "delivered",
          event_type: "customer_received",
          tracking_number: shipment.tracking_number,
          scan_code: shipment.scan_code,
          delivery_signature_name: customerName,
          delivery_signature_data_url: signature,
        }),
      });
      if (res.ok) {
        setResultMsg("Confirmation request sent. Status will update after approval.");
      } else {
        setError("Failed to send confirmation request.");
      }
    } catch {
      setError("Failed to send confirmation request.");
    }
  }

  return (
    <LogisticsPartnerLayout title="Scan">
      <PanelContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-text">Scan Shipment</h1>
            <p className="text-xs text-text-muted">Look up and confirm deliveries on the spot</p>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
            Scan code
            <input
              value={codeInput}
              onChange={(e) => setCodeInput(e.target.value)}
              placeholder="ORDER-xxx / SHIP-xxx"
              className="w-64 rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
            />
          </label>
          <button
            type="button"
            onClick={() => lookup(codeInput)}
            disabled={loading}
            className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold"
          >
            <ScanLine className="mr-1 inline h-3.5 w-3.5" />
            Lookup
          </button>
        </div>

        {loading && <p className="text-xs text-text-muted">Looking up shipment…</p>}
        {error && (
          <div className="rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">
            {error}
          </div>
        )}
        {resultMsg && (
          <div className="rounded-xl border border-success/30 bg-success/5 px-3 py-2 text-xs text-success">
            {resultMsg}
          </div>
        )}

        {shipment ? (
          <div className="space-y-3 rounded-xl border border-border bg-surface p-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-text">Shipment #{shipment.id}</h2>
              <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-medium text-warning">
                {shipment.status_label || shipment.status}
              </span>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-xs text-text-muted">
              <div>Order: <span className="text-text">#{shipment.order_id}</span></div>
              <div>Tracking: <span className="text-text">{shipment.tracking_number || "—"}</span></div>
              <div>Hub: <span className="text-text">{shipment.current_hub || "—"}</span></div>
              <div>Address: <span className="text-text">{shipment.shipping_address || "—"}</span></div>
            </dl>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setRequestedStatus("delivered")}
                className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold"
              >
                Delivered
              </button>
              <button
                type="button"
                onClick={sendConfirmationRequest}
                className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold"
              >
                Send Confirmation Request
              </button>
            </div>

            <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
              Customer full name
              <input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Customer full name"
                className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
              />
            </label>

            <div className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
              Customer signature
              <SignaturePad onChange={setSignature} />
            </div>
          </div>
        ) : (
          !loading && !error && (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <Truck className="h-8 w-8 text-text-faint" />
              <p className="text-sm text-text-muted">Scan a code to load the shipment.</p>
            </div>
          )
        )}
      </PanelContent>
    </LogisticsPartnerLayout>
  );
}

export default function LogisticsPartnerScanPage() {
  return (
    <Suspense fallback={<div className="p-4 text-sm text-text-muted">Loading…</div>}>
      <LogisticsPartnerScanInner />
    </Suspense>
  );
}
