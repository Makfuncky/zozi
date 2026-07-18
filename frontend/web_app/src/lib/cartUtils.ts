import { CartItem } from "./cartStore";

export interface Coupon {
  id: number;
  code: string;
  discount_type: "percent" | "fixed";
  value: number;
  min_order?: number;
  is_active?: boolean;
  uses_count?: number;
  max_uses?: number;
}

export interface ShippingRules {
  freeOver?: number;
  flatRate?: number;
}

export function calculateCartTotals(options: {
  items: CartItem[];
  coupon?: Coupon | null;
  shippingRules?: ShippingRules;
  taxRatePercent?: number;
}) {
  const { items, coupon = null, shippingRules = {}, taxRatePercent = 0 } = options;

  const subtotal = items.reduce((s, i) => s + Number(i.price ?? 0) * (i.quantity ?? 0), 0);

  // Compute discount
  let discount = 0;
  if (coupon && coupon.is_active) {
    if (coupon.min_order && subtotal < coupon.min_order) {
      discount = 0;
    } else if (coupon.discount_type === "percent") {
      discount = (subtotal * (coupon.value || 0)) / 100;
    } else {
      discount = coupon.value || 0;
    }
  }

  // Shipping
  const freeOver = shippingRules.freeOver ?? 0;
  const flatRate = shippingRules.flatRate ?? 0;
  const shipping = freeOver > 0 && subtotal >= freeOver ? 0 : flatRate;

  // VAT is applied to the discounted merchandise subtotal; delivery is added after tax.
  const taxable = Math.max(0, subtotal - discount);
  const vat = (taxable * (taxRatePercent || 0)) / 100;

  const total = subtotal - discount + shipping + vat;

  return {
    subtotal,
    discount,
    shipping,
    vat,
    total,
  };
}

export default calculateCartTotals;
