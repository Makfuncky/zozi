import {
  calculateCartSubtotal,
  calculateCartItemCount,
  calculateShippingCost,
  calculatePromoDiscount,
  calculateCartTotal,
  CartItem,
} from "./cartHelpers";
import type { Coupon } from "./types";

const item = (price: number, qty: number): CartItem => ({ price, quantity: qty });

const makeCoupon = (type: "fixed" | "percent", value: number, minOrder = 0): Coupon => ({
  id: 1,
  code: "TEST",
  discount_type: type,
  value,
  min_order: minOrder,
  is_active: true,
  uses_count: 0,
});

describe("calculateCartSubtotal", () => {
  it("returns 0 for empty cart", () => {
    expect(calculateCartSubtotal([])).toBe(0);
  });

  it("sums price × quantity for each item", () => {
    const items = [item(10, 2), item(5, 3)];
    expect(calculateCartSubtotal(items)).toBeCloseTo(35);
  });

  it("handles single item", () => {
    expect(calculateCartSubtotal([item(99.99, 1)])).toBeCloseTo(99.99);
  });
});

describe("calculateCartItemCount", () => {
  it("returns 0 for empty cart", () => {
    expect(calculateCartItemCount([])).toBe(0);
  });

  it("sums quantities across items", () => {
    expect(calculateCartItemCount([item(10, 2), item(5, 3)])).toBe(5);
  });
});

describe("calculateShippingCost", () => {
  it("returns 0 for free shipping threshold met", () => {
    expect(calculateShippingCost(100, 50, 5.99)).toBe(0);
  });

  it("returns standard rate below threshold", () => {
    expect(calculateShippingCost(30, 50, 5.99)).toBeCloseTo(5.99);
  });

  it("returns 0 for empty cart (subtotal=0)", () => {
    expect(calculateShippingCost(0)).toBe(0);
  });
});

describe("calculatePromoDiscount", () => {
  it("returns 0 with no coupon", () => {
    expect(calculatePromoDiscount(100)).toBe(0);
  });

  it("applies percentage discount", () => {
    const coupon = makeCoupon("percent", 10);
    expect(calculatePromoDiscount(200, coupon)).toBeCloseTo(20);
  });

  it("applies fixed discount", () => {
    const coupon = makeCoupon("fixed", 25);
    expect(calculatePromoDiscount(200, coupon)).toBeCloseTo(25);
  });

  it("clamps fixed discount to subtotal (no negative)", () => {
    const coupon = makeCoupon("fixed", 50);
    expect(calculatePromoDiscount(10, coupon)).toBeCloseTo(10);
  });

  it("respects min_order — no discount if below", () => {
    const coupon = makeCoupon("percent", 10, 100);
    expect(calculatePromoDiscount(50, coupon)).toBe(0);
  });

  it("returns 0 for inactive coupon", () => {
    const coupon = { ...makeCoupon("percent", 10), is_active: false };
    expect(calculatePromoDiscount(100, coupon)).toBe(0);
  });
});

describe("calculateCartTotal", () => {
  it("computes full totals object", () => {
    const items = [item(50, 2), item(10, 1)];
    const result = calculateCartTotal({ items });
    expect(result.subtotal).toBeCloseTo(110);
    expect(result.itemCount).toBe(3);
    expect(typeof result.total).toBe("number");
    expect(typeof result.shipping).toBe("number");
  });

  it("applies coupon discount in total", () => {
    const items = [item(100, 1)];
    const coupon = makeCoupon("percent", 10);
    const result = calculateCartTotal({ items, coupon });
    expect(result.discount).toBeCloseTo(10);
    expect(result.total).toBeLessThan(100);
  });

  it("handles empty cart", () => {
    const result = calculateCartTotal({ items: [] });
    expect(result.subtotal).toBe(0);
    expect(result.itemCount).toBe(0);
    expect(result.total).toBe(0);
  });

  it("applies tax rate", () => {
    const items = [item(100, 1)];
    const result = calculateCartTotal({ items, taxRatePercent: 5 });
    expect(result.tax).toBeGreaterThan(0);
  });
});

