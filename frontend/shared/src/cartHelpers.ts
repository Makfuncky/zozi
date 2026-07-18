import { OrderItem, Coupon } from "./types";

export type CartItem = Pick<OrderItem, "price" | "quantity">;

export type CartTotals = {
  itemCount: number;
  subtotal: number;
  discount: number;
  shipping: number;
  tax: number;
  total: number;
};

export function calculateCartItemCount(items: CartItem[] = []): number {
  return items.reduce((count, item) => count + (item.quantity ?? 0), 0);
}

export function calculateCartSubtotal(items: CartItem[] = []): number {
  return items.reduce((sum, item) => sum + item.price * (item.quantity ?? 0), 0);
}

export function calculateShippingCost(subtotal: number, freeOver = 50, standardRate = 5.99): number {
  if (subtotal <= 0) return 0;
  return subtotal >= freeOver ? 0 : standardRate;
}

export function calculatePromoDiscount(subtotal: number, coupon?: Coupon | null): number {
  if (!coupon || !coupon.is_active) return 0;
  if (coupon.min_order && subtotal < coupon.min_order) return 0;

  if (coupon.discount_type === "fixed") {
    return Math.min(subtotal, coupon.value);
  }

  if (coupon.discount_type === "percent") {
    return Math.min(subtotal, (subtotal * coupon.value) / 100);
  }

  return 0;
}

export function getAddToCartLabel(inStock: boolean): string {
  return inStock ? "Add to Cart" : "Out of Stock";
}

export function calculateCartTotal(params: {
  items: CartItem[];
  coupon?: Coupon | null;
  shippingOptions?: { freeOver?: number; standardRate?: number };
  taxRatePercent?: number;
}): CartTotals {
  const subtotal = calculateCartSubtotal(params.items);
  const shipping = calculateShippingCost(subtotal, params.shippingOptions?.freeOver ?? 50, params.shippingOptions?.standardRate ?? 5.99);
  const discount = calculatePromoDiscount(subtotal, params.coupon);
  const taxable = Math.max(0, subtotal - discount + shipping);
  const tax = Number(((taxable * (params.taxRatePercent ?? 0)) / 100).toFixed(2));
  const total = Number(Math.max(0, taxable + tax).toFixed(2));
  const itemCount = calculateCartItemCount(params.items);

  return {
    itemCount,
    subtotal: Number(subtotal.toFixed(2)),
    discount: Number(discount.toFixed(2)),
    shipping: Number(shipping.toFixed(2)),
    tax,
    total,
  };
}
