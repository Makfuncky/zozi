import { Order } from "./types";

export type OrderStatusKey = "pending" | "confirmed" | "processing" | "prepared" | "picking_up" | "shipped" | "delivered" | "cancelled" | "failed" | "returned" | "refunded" | "completed";

export const ORDER_STATUS_VARIANTS: Record<OrderStatusKey, "success" | "warning" | "danger" | "info" | "default"> = {
  pending: "warning",
  confirmed: "success",
  processing: "info",
  prepared: "info",
  picking_up: "info",
  shipped: "info",
  delivered: "success",
  completed: "success",
  cancelled: "danger",
  failed: "danger",
  returned: "danger",
  refunded: "danger",
};

export const ORDER_STATUS_LABEL: Record<OrderStatusKey, string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  processing: "Processing",
  prepared: "Prepared",
  picking_up: "Picking Up",
  shipped: "Shipped",
  delivered: "Delivered",
  completed: "Completed",
  cancelled: "Cancelled",
  failed: "Failed",
  returned: "Returned",
  refunded: "Refunded",
};

export function normalizeOrderStatus(status?: string): OrderStatusKey {
  if (!status) return "pending";
  const key = status.toLowerCase() as OrderStatusKey;
  if (Object.prototype.hasOwnProperty.call(ORDER_STATUS_VARIANTS, key)) {
    return key;
  }
  return "pending";
}

export function getOrderTotals(order: Order) {
  const subtotal = order.subtotal_amount ?? 0;
  const shipping = order.shipping_amount ?? 0;
  const vat = order.vat_amount ?? 0;
  const total = order.total_amount ?? order.total ?? subtotal + shipping + vat;
  return { subtotal, shipping, vat, total };
}
