import {
  CheckCircle2,
  Clock3,
  Truck,
} from "@/lib/icons";
import type { OrderTracking } from "@/lib/types";

export type SupplierOrder = {
  id: number;
  user_id: number;
  total_amount: number;
  status: string;
  created_at: string;
  customer_name: string;
  customer_email?: string | null;
  customer_phone?: string | null;
  shipping_address?: string | null;
  delivery_location?: string | null;
  delivery_note?: string | null;
  payment_status?: "paid" | "unpaid" | null;
  paid_at?: string | null;
  payment_method?: string | null;
  settlement_status?: string | null;
  settlement_id?: number | null;
  settlement_net_amount?: number | null;
  items: Array<{
    id: number;
    product_id: number;
    quantity: number;
    price: number;
    product_name: string;
    product_image?: string | null;
  }>;
};

export type ParcelProof = {
  id: number;
  result?: string | null;
  scan_code?: string | null;
  notes?: string | null;
  created_at?: string | null;
  image_urls?: string[] | null;
};

export type ShipmentForm = {
  current_hub: string;
  notes: string;
  package_count: string;
  package_weight_kg: string;
  package_dimensions: string;
  packaging_notes: string;
};

export const ORDER_STATUS_FILTERS = [
  "all",
  "pending",
  "confirmed",
  "processing",
  "prepared",
  "picking_up",
  "shipped",
  "delivered",
  "cancelled",
] as const;

export function createEmptyShipmentForm(): ShipmentForm {
  return {
    current_hub: "",
    notes: "",
    package_count: "",
    package_weight_kg: "",
    package_dimensions: "",
    packaging_notes: "",
  };
}

export function formatDate(value?: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString();
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function sentenceStatus(value?: string | null): string {
  if (!value) return "Pending";
  return value.replaceAll("_", " ");
}

export function titleStatus(value?: string | null): string {
  const normalized = sentenceStatus(value);
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

export function supplierWorkflowStatus(value?: string | null): string {
  if (!value) return "pending";
  return value === "confirmed" ? "pending" : value;
}

export function badgeClass(status?: string | null): string {
  switch (status) {
    case "delivered":
      return "theme-chip-success";
    case "shipped":
    case "in_transit":
    case "picking_up":
    case "prepared":
      return "theme-chip-brand";
    case "processing":
    case "confirmed":
      return "theme-chip-warning";
    case "cancelled":
    case "failed":
    case "returned":
      return "theme-chip-danger";
    default:
      return "theme-chip-muted";
  }
}

export function Timeline({
  tracking,
  statusOverride,
}: {
  tracking: OrderTracking;
  statusOverride?: string | null;
}) {
  const displayStatus = statusOverride || tracking.order_status;

  return (
    <div className="rounded-xl border border-border bg-surface-1 p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
            Order Progress
          </p>
          <p className="mt-1 text-xs font-semibold text-text">
            {titleStatus(displayStatus)}
          </p>
        </div>
        <div className="text-xs text-text-muted">
          {tracking.delivered_shipments}/{tracking.shipment_count} shipments delivered
        </div>
      </div>
      <div className="mt-4 flex items-start gap-0 overflow-x-auto pb-1">
        {tracking.timeline.map((step, index) => {
          const isLast = index === tracking.timeline.length - 1;
          return (
            <div key={step.key} className="flex min-w-[6.5rem] flex-1 items-center">
              <div className="flex shrink-0 flex-col items-center">
                <div
                  className={
                    `flex h-9 w-9 items-center justify-center rounded-full border-2 ${
                      step.completed
                        ? "border-success bg-success text-on-brand"
                        : step.active
                          ? "border-primary bg-primary/15 text-primary"
                          : "border-border bg-surface-2 text-text-faint"
                    }`
                  }
                >
                  {step.completed ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : step.active ? (
                    <Truck className="h-4 w-4" />
                  ) : (
                    <Clock3 className="h-4 w-4" />
                  )}
                </div>
                <span
                  className={
                    `mt-1 text-center text-[10px] uppercase tracking-wide ${
                      step.completed
                        ? "theme-status-success"
                        : step.active
                          ? "theme-status-info font-semibold"
                          : "text-text-faint"
                    }`
                  }
                >
                  {step.label}
                </span>
              </div>
              {!isLast ? (
                <div
                  className={`mb-4 h-0.5 flex-1 ${
                    step.completed
                      ? "bg-success"
                      : step.active
                        ? "bg-primary/35"
                        : "bg-border"
                  }`}
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}


