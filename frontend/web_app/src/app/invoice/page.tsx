"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import BrandLoading from "@/components/BrandLoading";
import { useCurrencyStore } from "@/lib/currencyStore";

type InvoicePayload = {
  id: number;
  invoice_number: string;
  order_id: number;
  created_at: string;
  status: string;
  customer_name: string;
  customer_email: string;
  customer_address: string;
  supplier_name: string;
  supplier_email?: string;
  items: Array<{
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    total: number;
  }>;
  subtotal: number;
  vat: number;
  shipping: number;
  total: number;
  logistics: Array<{
    stage: "supplier" | "warehouse" | "in_transit" | "delivered";
    label: string;
    timestamp?: string | null;
    notes?: string | null;
    completed: boolean;
  }>;
  tracking_number?: string;
  carrier?: string;
  scan_codes?: string[];
};

function InvoicePageClient() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const params = useSearchParams();
  const orderId = params?.get("order_id");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [invoice, setInvoice] = useState<InvoicePayload | null>(null);
  const [scanCode, setScanCode] = useState("");
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const id = Number(orderId);
    if (!id) {
      setError("Missing order_id query parameter.");
      setLoading(false);
      return;
    }

    apiFetch(`/orders/${id}/invoice`)
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          setError(data?.detail || "Could not load invoice.");
        } else {
          setInvoice(data as InvoicePayload);
          if ((data as InvoicePayload).scan_codes?.[0]) {
            setScanCode((data as InvoicePayload).scan_codes?.[0] || "");
          }
        }
      })
      .catch(() => setError("Could not load invoice."))
      .finally(() => setLoading(false));
  }, [orderId]);

  const confirmReceipt = async () => {
    if (!invoice || !scanCode.trim()) return;
    setConfirming(true);
    try {
      const res = await apiFetch(`/orders/${invoice.order_id}/scan-receipt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_code: scanCode.trim(), notes: "Web customer confirmation" }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || "Receipt confirmation failed.");
      } else {
        setError("");
        setInvoice({ ...invoice, status: "delivered" });
      }
    } catch {
      setError("Receipt confirmation failed.");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return <BrandLoading fullscreen label="Loading invoice..." />;
  }

  if (error && !invoice) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6">
        <div className="rounded-2xl border border-danger/40 bg-danger/10 px-6 py-5 text-danger">
          {error}
        </div>
      </main>
    );
  }

  if (!invoice) {
    return null;
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="rounded-2xl border border-border bg-surface-1 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-text">Invoice #{invoice.invoice_number}</h1>
              <p className="text-sm text-text-muted">
                Order #{invoice.order_id} · {invoice.created_at?.slice(0, 10)}
              </p>
            </div>
            <span className="rounded-lg bg-primary/15 px-3 py-1 text-xs font-semibold text-primary">
              {invoice.status.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-border bg-surface-1 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Supplier</p>
            <p className="mt-1 text-sm font-semibold text-text">{invoice.supplier_name}</p>
            {invoice.supplier_email && <p className="text-sm text-text-muted">{invoice.supplier_email}</p>}
          </div>
          <div className="rounded-2xl border border-border bg-surface-1 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">Customer</p>
            <p className="mt-1 text-sm font-semibold text-text">{invoice.customer_name}</p>
            <p className="text-sm text-text-muted">{invoice.customer_address}</p>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-surface-1 p-4">
          <h2 className="text-sm font-bold text-text">Supply Chain Timeline</h2>
          <div className="mt-3 space-y-2">
            {invoice.logistics.map((step) => (
              <div key={step.stage} className="flex items-start gap-3 rounded-xl border border-border/60 bg-surface-2/40 p-3">
                <div className={`mt-0.5 h-2.5 w-2.5 rounded-full ${step.completed ? "bg-success" : "bg-border"}`} />
                <div>
                  <p className="text-sm font-semibold text-text">{step.label}</p>
                  {step.timestamp && (
                    <p className="text-xs text-text-muted">{step.timestamp.replace("T", " ").slice(0, 16)}</p>
                  )}
                  {step.notes && <p className="text-xs text-text-muted">{step.notes}</p>}
                </div>
              </div>
            ))}
          </div>
          {invoice.tracking_number && (
            <p className="mt-3 text-sm text-text-muted">
              Tracking: <span className="font-semibold text-text">{invoice.tracking_number}</span>
              {invoice.carrier ? ` · ${invoice.carrier}` : ""}
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-border bg-surface-1 p-4">
          <h2 className="text-sm font-bold text-text">Items</h2>
          <div className="mt-3 space-y-2">
            {invoice.items.map((item) => (
              <div key={item.product_id} className="flex items-center justify-between rounded-xl border border-border/60 bg-surface-2/40 px-3 py-2">
                <div>
                  <p className="text-sm font-semibold text-text">{item.product_name}</p>
                  <p className="text-xs text-text-muted">
                    {item.quantity} x {formatMoney(Number(item.unit_price))}
                  </p>
                </div>
                <p className="text-sm font-semibold text-text">{formatMoney(Number(item.total))}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-1 border-t border-border pt-3 text-sm">
            <div className="flex justify-between text-text-muted">
              <span>Subtotal</span>
              <span>{formatMoney(Number(invoice.subtotal))}</span>
            </div>
            <div className="flex justify-between text-text-muted">
              <span>VAT</span>
              <span>{formatMoney(Number(invoice.vat))}</span>
            </div>
            <div className="flex justify-between text-text-muted">
              <span>Shipping</span>
              <span>{formatMoney(Number(invoice.shipping))}</span>
            </div>
            <div className="flex justify-between font-bold text-text">
              <span>Total</span>
              <span>{formatMoney(Number(invoice.total))}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-surface-1 p-4">
          <h2 className="text-sm font-bold text-text">Customer Receipt Scan</h2>
          <p className="mt-1 text-xs text-text-muted">
            Confirm final delivery by scanning or pasting the shipment scan code.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <input
              value={scanCode}
              onChange={(e) => setScanCode(e.target.value)}
              className="theme-input min-w-64 flex-1 rounded-xl border px-3 py-2 text-sm focus:border-primary focus:outline-none"
              placeholder="SHIP-204"
            />
            <button
              onClick={confirmReceipt}
              disabled={confirming || !scanCode.trim()}
              className="rounded-xl theme-btn-primary px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              {confirming ? "Confirming..." : "Confirm Receipt"}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-sm text-danger">{error}</p>
          )}
        </div>
      </div>
    </main>
  );
}

export default function InvoicePage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center text-text-muted">
          Loading invoice...
        </main>
      }
    >
      <InvoicePageClient />
    </Suspense>
  );
}


