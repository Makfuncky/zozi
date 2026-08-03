"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import QRCode from "qrcode";
import SupplierLayout from "@/components/SupplierLayout";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import type { SupplierLabelPayload } from "@/lib/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

function parseLatLng(value?: string | null): { latitude?: string; longitude?: string } {
  if (!value) return {};
  const parts = value.split(",").map((part) => part.trim()).filter(Boolean);
  if (parts.length >= 2) {
    return { latitude: parts[0], longitude: parts[1] };
  }
  return {};
}

function formatDateTime(value?: string | null): string {
  if (!value) return "Not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function formatReference(prefix: string, value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "Pending";
  const raw = String(value).trim();
  if (!raw) return "Pending";
  const numeric = Number(raw);
  if (!Number.isNaN(numeric) && Number.isInteger(numeric)) {
    return `${prefix}-${String(numeric).padStart(6, "0")}`;
  }
  return raw.toUpperCase().startsWith(`${prefix}-`) ? raw.toUpperCase() : `${prefix}-${raw}`;
}

function formatPaymentMethod(value?: string | null): string {
  if (!value) return "Not specified";
  const normalized = value.replaceAll("_", " ").trim().toLowerCase();
  if (normalized === "cod") return "Cash on Delivery";
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatPackageValue<T extends string | number>(
  value: T | null | undefined,
  emptyLabel: string,
  formatter?: (resolved: T) => string,
): string {
  if (value === null || value === undefined || value === "") return emptyLabel;
  return formatter ? formatter(value) : String(value);
}

export default function SupplierLabelPrintPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const formatMoney = useCurrencyStore((state) => state.format);
  const currencyCode = useCurrencyStore((state) => state.currency.code);
  const [label, setLabel] = useState<SupplierLabelPayload | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [printMode, setPrintMode] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || user?.role !== "supplier") {
      router.push("/supplier/login");
      return;
    }

    apiFetch(`/supplier/orders/${id}/label`)
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          setError(payload?.detail || "Could not load parcel sheet.");
          return;
        }
        const labelPayload = (await response.json()) as SupplierLabelPayload;
        setLabel(labelPayload);
      })
      .catch(() => setError("Could not load parcel sheet."))
      .finally(() => setLoading(false));
  }, [authLoading, id, isLoggedIn, router, user?.role]);

  useEffect(() => {
    if (!label?.scan_code) {
      setQrDataUrl("");
      return;
    }
    QRCode.toDataURL(label.scan_code, {
      margin: 1,
      width: 220,
      color: { dark: "#000000", light: "#ffffff" },
    })
      .then(setQrDataUrl)
      .catch(() => setQrDataUrl(""));
  }, [label?.scan_code]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const enterPrintMode = () => setPrintMode(true);
    const exitPrintMode = () => setPrintMode(false);
    const mediaQuery = window.matchMedia("print");
    const handleMediaQueryChange = (event: MediaQueryListEvent) => setPrintMode(event.matches);

    window.addEventListener("beforeprint", enterPrintMode);
    window.addEventListener("afterprint", exitPrintMode);
    mediaQuery.addEventListener("change", handleMediaQueryChange);

    return () => {
      window.removeEventListener("beforeprint", enterPrintMode);
      window.removeEventListener("afterprint", exitPrintMode);
      mediaQuery.removeEventListener("change", handleMediaQueryChange);
    };
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return undefined;
    document.body.classList.toggle("supplier-label-print", printMode);
    return () => {
      document.body.classList.remove("supplier-label-print");
    };
  }, [printMode]);

  if (loading || authLoading) {
    return <SupplierLayout title="Print Parcel Sheet"><div className="p-6 text-sm text-text-muted">Loading parcel sheet...</div></SupplierLayout>;
  }

  if (error || !label) {
    return (
      <SupplierLayout title="Print Parcel Sheet">
        <div className="theme-card rounded-2xl border p-6 text-center">
          <p className="text-sm text-danger">{error || "No supplier shipment found for this order."}</p>
          <button onClick={() => router.back()} className="mt-4 theme-link-brand text-sm">Go Back</button>
        </div>
      </SupplierLayout>
    );
  }

  const { latitude, longitude } = parseLatLng(label.delivery_location);
  const sheetHeading = label.has_shipment ? "ZOZI Parcel Sheet" : "ZOZI Packing Sheet";
  const statusHeading = label.has_shipment ? "Supplier Shipment Status" : "Fulfilment Status";
  const statusValue = label.has_shipment
    ? label.shipment_status_label || label.shipment_status.replaceAll("_", " ")
    : "Awaiting shipment creation";
  const qrHeading = label.has_shipment ? "Parcel QR Code" : "Order QR Code";
  const scanHeading = label.has_shipment ? "Shipment Scan Code" : "Order Scan Code";
  const displayTrackingNumber = label.tracking_number || (label.has_shipment ? label.scan_code : null);
  const orderReference = formatReference("ORD", label.order_id);
  const shipmentReference = label.has_shipment ? formatReference("SHP", label.shipment_id) : "Pending booking";
  const coordinatePair = [latitude, longitude].filter(Boolean).join(", ");
  const supplierName = label.supplier_name || user?.username || "Supplier";
  const shippingLabel = label.has_shipment ? "Delivery Charges" : "Projected Delivery Charges";
  const packageCountLabel = formatPackageValue(label.package_count, "To be confirmed during shipment booking");
  const packageWeightLabel = formatPackageValue(label.package_weight_kg, "To be measured after packing", (value) => `${value} kg`);
  const packageDimensionsLabel = formatPackageValue(label.package_dimensions, "To be added after packing");
  const packagedAtLabel = label.packaged_at ? formatDateTime(label.packaged_at) : "Will be stamped after final packing";
  const packagingNotesLabel = label.packaging_notes || "Handled by supplier fulfilment team.";
  const customerAddressLabel = label.shipping_address || "Customer delivery address not provided.";
  const paymentMethodLabel = formatPaymentMethod(label.payment_method);
  const orderedAtLabel = formatDateTime(label.ordered_at);
  const paidAtLabel = label.paid_at ? formatDateTime(label.paid_at) : "Awaiting payment confirmation";
  const qrAlt = `${sheetHeading} QR for ${label.scan_code}`;

  const handlePrint = () => {
    setPrintMode(true);
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        window.print();
      });
    });
  };

  const sheet = (
    <div className="mx-auto max-w-5xl rounded-4xl border border-border bg-surface p-8 text-text shadow-card-xl print:max-w-none print:rounded-none print:border-0 print:bg-white print:p-0 print:text-black print:shadow-none">
      <div className="rounded-[1.75rem] border border-border bg-[linear-gradient(135deg,color-mix(in_srgb,var(--color-surface-2)_84%,transparent)_0%,color-mix(in_srgb,var(--color-surface-0)_92%,transparent)_45%,color-mix(in_srgb,var(--color-brand)_14%,transparent)_100%)] p-6 print:rounded-none print:border-0 print:bg-none print:p-0">
        <div className="flex flex-wrap items-start justify-between gap-6 border-b border-border pb-6 print:border-neutral-300">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              {label.supplier_logo_url ? (
                <img src={label.supplier_logo_url} alt={supplierName} className="h-12 w-12 rounded-2xl border border-border object-cover print:border-neutral-300" />
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-sm font-black tracking-[0.35em] text-on-brand print:bg-black print:text-white">Z</div>
              )}
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-text-faint print:text-neutral-500">ZOZI Supplier Network</p>
                <h1 className="text-3xl font-black tracking-tight text-text print:text-black">{sheetHeading}</h1>
              </div>
            </div>
            <div className="space-y-1 text-sm text-text-muted print:text-neutral-700">
              <p className="font-semibold text-text print:text-black">Issued by {supplierName}</p>
              {label.supplier_address ? <p>{label.supplier_address}</p> : null}
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {label.supplier_email ? <span>{label.supplier_email}</span> : null}
                {label.supplier_phone ? <span>{label.supplier_phone}</span> : null}
                {label.supplier_website ? <span>{label.supplier_website}</span> : null}
              </div>
              {label.supplier_tax_id ? <p>Tax / Registration ID: {label.supplier_tax_id}</p> : null}
            </div>
          </div>

          <div className="grid min-w-70 gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-border bg-surface/90 p-4 print:border-neutral-300 print:bg-white">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Invoice</p>
              <p className="mt-2 text-lg font-bold text-text print:text-black">{label.invoice_number}</p>
              <p className="mt-1 text-xs text-text-faint print:text-neutral-500">Issued {orderedAtLabel}</p>
            </div>
            <div className="rounded-2xl border border-primary/20 bg-primary/10 p-4 text-text print:border-neutral-300 print:bg-white print:text-black">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Status</p>
              <p className="mt-2 text-lg font-bold">{statusValue}</p>
              <p className="mt-1 text-xs text-text-faint print:text-neutral-500">{statusHeading}</p>
            </div>
            <div className="rounded-2xl border border-border bg-surface/90 p-4 print:border-neutral-300 print:bg-white">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Order Reference</p>
              <p className="mt-2 text-base font-bold text-text print:text-black">{orderReference}</p>
              <p className="mt-1 text-xs text-text-faint print:text-neutral-500">Shipment: {shipmentReference}</p>
            </div>
            <div className="rounded-2xl border border-border bg-surface/90 p-4 print:border-neutral-300 print:bg-white">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Payment</p>
              <p className="mt-2 text-base font-bold text-text print:text-black">{paymentMethodLabel}</p>
              <p className="mt-1 text-xs text-text-faint print:text-neutral-500">{paidAtLabel}</p>
            </div>
          </div>
        </div>

        {!label.has_shipment ? (
          <div className="theme-alert-warning mt-5 rounded-2xl px-4 py-3 text-sm print:border-neutral-300 print:bg-neutral-100 print:text-black">
            Shipment booking is still pending. This invoice already reflects the supplier-side order lines, while carrier assignment, final parcel weight, and dispatch details will be stamped once fulfilment is booked from the supplier orders workspace.
          </div>
        ) : null}

        <div className="mt-6 grid gap-5 lg:grid-cols-[1.6fr_1fr] print:grid-cols-[1.55fr_1fr]">
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-border bg-surface p-5 print:border-neutral-300 print:bg-white">
                <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Bill To</p>
                <div className="mt-3 space-y-1.5 text-sm text-text-muted print:text-neutral-700">
                  <p className="text-base font-bold text-text print:text-black">{label.customer_name}</p>
                  {label.customer_email ? <p>{label.customer_email}</p> : null}
                  {label.customer_phone ? <p>{label.customer_phone}</p> : null}
                  <p>{customerAddressLabel}</p>
                  {label.delivery_note ? <p>Delivery Note: {label.delivery_note}</p> : null}
                  {coordinatePair ? <p>Coordinates: {coordinatePair}</p> : null}
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-surface p-5 print:border-neutral-300 print:bg-white">
                <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Shipment Details</p>
                <div className="mt-3 grid gap-2 text-sm text-text-muted print:text-neutral-700">
                  <p><span className="font-semibold text-text print:text-black">Carrier:</span> {label.carrier_name || "Awaiting carrier assignment"}</p>
                  <p><span className="font-semibold text-text print:text-black">Tracking:</span> {displayTrackingNumber || "Generated after booking"}</p>
                  <p><span className="font-semibold text-text print:text-black">Current Hub:</span> {label.current_hub || "Awaiting dispatch"}</p>
                  <p><span className="font-semibold text-text print:text-black">Package Count:</span> {packageCountLabel}</p>
                  <p><span className="font-semibold text-text print:text-black">Weight:</span> {packageWeightLabel}</p>
                  <p><span className="font-semibold text-text print:text-black">Dimensions:</span> {packageDimensionsLabel}</p>
                  <p><span className="font-semibold text-text print:text-black">Packed At:</span> {packagedAtLabel}</p>
                  <p><span className="font-semibold text-text print:text-black">Packing Notes:</span> {packagingNotesLabel}</p>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-3xl border border-border bg-surface print:border-neutral-300 print:bg-white">
              <div className="border-b border-border px-5 py-4 print:border-neutral-300">
                <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Invoice Items</p>
                <p className="mt-1 text-sm text-text-muted print:text-neutral-700">Supplier-scoped order lines prepared for fulfilment and customer billing.</p>
              </div>
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-2 text-text-faint print:bg-neutral-100 print:text-neutral-500">
                  <tr>
                    <th className="px-5 py-3 font-semibold">Item</th>
                    <th className="px-4 py-3 font-semibold">Qty</th>
                    <th className="px-4 py-3 font-semibold">Unit Price</th>
                    <th className="px-5 py-3 text-right font-semibold">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {label.items.map((item, index) => (
                    <tr
                      key={item.order_item_id ?? `${item.product_id}-${item.product_name}-${index}`}
                      className="border-t border-border align-top print:border-neutral-300"
                    >
                      <td className="px-5 py-4">
                        <p className="font-semibold text-text print:text-black">{item.product_name}</p>
                        <p className="mt-1 text-xs text-text-faint print:text-neutral-500">SKU Ref #{item.product_id}</p>
                      </td>
                      <td className="px-4 py-4 text-text-muted print:text-neutral-700">{item.quantity}</td>
                      <td className="px-4 py-4 text-text-muted print:text-neutral-700">{formatMoney(Number(item.unit_price))}</td>
                      <td className="px-5 py-4 text-right font-semibold text-text print:text-black">{formatMoney(Number(item.line_total))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-3xl border border-border bg-surface-2 p-5 text-text print:border-neutral-300 print:bg-white print:text-black">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Scan & Verify</p>
              <div className="mt-4 flex justify-center rounded-[1.25rem] bg-white p-4 border border-border print:border-neutral-300">
                {qrDataUrl ? (
                  <img src={qrDataUrl} alt={qrAlt} className="h-44 w-44 object-contain" />
                ) : (
                  <div className="flex h-44 w-44 items-center justify-center rounded-xl border border-dashed border-border text-sm text-text-faint print:border-neutral-300 print:text-neutral-500">
                    QR unavailable
                  </div>
                )}
              </div>
              <div className="mt-4 space-y-3 text-center">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">{scanHeading}</p>
                  <p className="mt-1 break-all font-mono text-sm font-semibold">{label.scan_code}</p>
                </div>
                {displayTrackingNumber ? (
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Tracking Reference</p>
                    <p className="mt-1 break-all font-mono text-sm font-semibold">{displayTrackingNumber}</p>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="rounded-3xl border border-border bg-surface p-5 print:border-neutral-300 print:bg-white">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Invoice Summary</p>
              <div className="mt-4 space-y-3 text-sm text-text-muted print:text-neutral-700">
                <div className="flex items-center justify-between">
                  <span>Subtotal</span>
                  <span className="font-semibold text-text print:text-black">{formatMoney(label.subtotal)}</span>
                </div>
                {(label.discount ?? 0) > 0 ? (
                  <div className="flex items-center justify-between">
                    <span>Discount Allocation</span>
                    <span className="font-semibold text-success">- {formatMoney(label.discount ?? 0)}</span>
                  </div>
                ) : null}
                <div className="flex items-center justify-between">
                  <span>VAT</span>
                  <span className="font-semibold text-text print:text-black">{formatMoney(label.vat)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>{shippingLabel}</span>
                  <span className="font-semibold text-text print:text-black">{formatMoney(label.shipping)}</span>
                </div>
              </div>
              <div className="mt-4 rounded-2xl bg-primary/10 px-4 py-4 text-text border border-primary/20 print:border-neutral-300 print:bg-neutral-100 print:text-black">
                <div className="flex items-center justify-between text-sm text-text-faint print:text-neutral-500">
                  <span>Total Due</span>
                  <span>{currencyCode}</span>
                </div>
                <p className="mt-2 text-3xl font-black tracking-tight">{formatMoney(label.total)}</p>
              </div>
            </div>

            <div className="rounded-3xl border border-border bg-surface p-5 text-sm text-text-muted print:border-neutral-300 print:bg-white print:text-neutral-700">
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-text-faint print:text-neutral-500">Document Notes</p>
              <div className="mt-3 space-y-2">
                <p>This document was generated through the ZOZI supplier fulfilment desk for packing, shipment handoff, and customer billing reference.</p>
                <p>Order status: <span className="font-semibold text-text print:text-black">{label.order_status.replaceAll("_", " ")}</span></p>
                <p>Contact support with invoice reference <span className="font-semibold text-text print:text-black">{label.invoice_number}</span> for any fulfilment discrepancy.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (printMode) {
    return (
      <>
        <div className="supplier-label-print-root min-h-screen bg-white px-4 py-5 text-black print:min-h-0 print:px-0 print:py-0">{sheet}
        </div>
      </>
    );
  }

  return (
    <SupplierLayout title="Print Parcel Sheet">
      <div className="flex items-center justify-between gap-3 mb-4 print:hidden">
        <button onClick={() => router.back()} className="theme-action-secondary rounded-xl px-4 py-2 text-sm font-semibold">Back</button>
        <button onClick={handlePrint} className="theme-btn-primary rounded-xl px-4 py-2 text-sm font-semibold">Print Sheet</button>
      </div>
      {sheet}
    </SupplierLayout>
  );
}