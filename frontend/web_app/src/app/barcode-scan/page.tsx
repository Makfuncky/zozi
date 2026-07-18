"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import BrandLoading from "@/components/BrandLoading";
import { useCurrencyStore } from "@/lib/currencyStore";

type ScanTarget = "product" | "transaction";

type ProductResult = {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
};

type ShipmentResult = {
  shipment: {
    id: number;
    order_id: number;
    status: string;
    distribution_channel?: string;
    current_hub?: string;
  };
  event: {
    id: number;
    event_type: string;
    status_after?: string;
    location?: string;
    created_at: string;
  };
};

const SHIPMENT_EVENT_TYPES = [
  "picked_from_supplier",
  "logistics_received",
  "distribution_checkpoint",
  "out_for_delivery",
  "customer_received",
  "shipment_failed",
  "shipment_returned",
] as const;

function BarcodeScanPageClient() {
  const params = useSearchParams();
  const formatMoney = useCurrencyStore((s) => s.format);
  const [target, setTarget] = useState<ScanTarget>("product");
  const [code, setCode] = useState("");
  const [eventType, setEventType] = useState<typeof SHIPMENT_EVENT_TYPES[number]>("distribution_checkpoint");
  const [location, setLocation] = useState("");
  const [distributionChannel, setDistributionChannel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [product, setProduct] = useState<ProductResult | null>(null);
  const [shipment, setShipment] = useState<ShipmentResult | null>(null);

  useEffect(() => {
    const initial = params?.get("code");
    if (initial) setCode(initial);
  }, [params]);

  const handleLookup = async () => {
    const trimmed = code.trim();
    if (!trimmed) return;

    setLoading(true);
    setError("");
    setProduct(null);
    setShipment(null);
    try {
      if (target === "transaction") {
        const match = trimmed.toUpperCase().match(/^SHIP-(\d+)$/);
        if (!match) {
          setError("Transaction code must be SHIP-<id>.");
        } else {
          const shipmentId = Number(match[1]);
          const res = await apiFetch(`/logistics/shipments/${shipmentId}/scan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              scan_code: trimmed,
              event_type: eventType,
              location: location || undefined,
              distribution_channel: distributionChannel || undefined,
            }),
          });
          const data = await res.json();
          if (!res.ok) {
            setError(data?.detail || "Failed to record shipment scan.");
          } else {
            setShipment(data as ShipmentResult);
          }
        }
      } else {
        const res = await apiFetch(`/products/barcode/${encodeURIComponent(trimmed)}`);
        const data = await res.json();
        if (!res.ok) {
          setError(data?.detail || "No product found.");
        } else {
          setProduct(data as ProductResult);
        }
      }
    } catch {
      setError("Scan lookup failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto w-full max-w-2xl space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-text">Barcode / QR Scanner</h1>
          <p className="mt-1 text-sm text-text-muted">
            Product lookups and supply-chain transaction scans.
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-surface-1 p-4 space-y-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTarget("product")}
              className={`rounded-xl px-3 py-1.5 text-xs font-semibold ${target === "product" ? "bg-primary text-on-brand" : "bg-surface-2 text-text-muted border border-border"}`}
            >
              Product
            </button>
            <button
              onClick={() => setTarget("transaction")}
              className={`rounded-xl px-3 py-1.5 text-xs font-semibold ${target === "transaction" ? "bg-primary text-on-brand" : "bg-surface-2 text-text-muted border border-border"}`}
            >
              Transaction
            </button>
          </div>

          {target === "transaction" && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-text-muted">Event type</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value as typeof SHIPMENT_EVENT_TYPES[number])}
                  className="theme-input w-full rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none"
                >
                  {SHIPMENT_EVENT_TYPES.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-muted">Distribution channel</label>
                <input
                  value={distributionChannel}
                  onChange={(e) => setDistributionChannel(e.target.value)}
                  placeholder="e.g. air_freight"
                  className="theme-input w-full rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs text-text-muted">Location / hub</label>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Dubai South Hub"
                  className="theme-input w-full rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none"
                />
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder={target === "transaction" ? "SHIP-204" : "P-42 or 42"}
              className="theme-input flex-1 rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
            <button
              onClick={handleLookup}
              disabled={loading || !code.trim()}
              className="rounded-xl theme-btn-primary px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              {loading ? "Processing..." : "Lookup"}
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {product && (
          <div className="rounded-2xl border border-border bg-surface-1 p-4">
            <h2 className="text-base font-bold text-text">{product.name}</h2>
            <p className="text-sm text-text-muted">{product.category}</p>
            <div className="mt-2 flex items-center gap-4 text-sm">
              <span className="font-semibold text-primary">{formatMoney(Number(product.price))}</span>
              <span className="text-text-muted">Stock: {product.stock}</span>
            </div>
          </div>
        )}

        {shipment && (
          <div className="rounded-2xl border border-border bg-surface-1 p-4">
            <h2 className="text-base font-bold text-text">
              Shipment #{shipment.shipment.id} · Order #{shipment.shipment.order_id}
            </h2>
            <p className="mt-1 text-sm text-text-muted">
              Event: {shipment.event.event_type} · Status: {shipment.shipment.status}
            </p>
            {shipment.event.location && (
              <p className="text-sm text-text-muted">Location: {shipment.event.location}</p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default function BarcodeScanPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen px-4 py-8">
          <div className="mx-auto w-full max-w-2xl">
            <div className="rounded-2xl border border-border bg-surface-1 p-8 text-sm text-text-muted">
              <BrandLoading label="Loading scanner..." />
            </div>
          </div>
        </main>
      }
    >
      <BarcodeScanPageClient />
    </Suspense>
  );
}


