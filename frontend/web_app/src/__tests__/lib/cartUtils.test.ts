/**
 * Tests for web_app/src/lib/cartUtils.ts — calculateCartTotals
 */

import { calculateCartTotals, Coupon, ShippingRules } from "@/lib/cartUtils";
import { CartItem } from "@/lib/cartStore";

function makeItem(price: number, qty: number = 1): CartItem {
  return {
    id: 1,
    name: "Test Product",
    price,
    image_url: "",
    description: "",
    category: "test",
    stock: 100,
    is_active: true,
    quantity: qty,
    line_id: `1::size::color`,
  } as CartItem;
}

const activeCoupon = (type: "percent" | "fixed", value: number, opts?: Partial<Coupon>): Coupon => ({
  id: 1,
  code: "DISCOUNT",
  discount_type: type,
  value,
  is_active: true,
  ...opts,
});

describe("calculateCartTotals", () => {
  it("returns zeros for an empty cart", () => {
    const result = calculateCartTotals({ items: [] });
    expect(result.subtotal).toBe(0);
    expect(result.discount).toBe(0);
    expect(result.shipping).toBe(0);
    expect(result.total).toBe(0);
  });

  it("computes subtotal for multiple items", () => {
    const items = [makeItem(10, 2), makeItem(5, 3)];
    const result = calculateCartTotals({ items });
    expect(result.subtotal).toBe(35); // 10*2 + 5*3
  });

  it("applies a percent coupon", () => {
    const items = [makeItem(100)];
    const coupon = activeCoupon("percent", 20);
    const result = calculateCartTotals({ items, coupon });
    expect(result.discount).toBe(20);
    expect(result.total).toBe(80);
  });

  it("applies a fixed coupon", () => {
    const items = [makeItem(100)];
    const coupon = activeCoupon("fixed", 15);
    const result = calculateCartTotals({ items, coupon });
    expect(result.discount).toBe(15);
    expect(result.total).toBe(85);
  });

  it("does not apply coupon below minimum order", () => {
    const items = [makeItem(30)];
    const coupon = activeCoupon("percent", 10, { min_order: 50 });
    const result = calculateCartTotals({ items, coupon });
    expect(result.discount).toBe(0);
    expect(result.total).toBe(30);
  });

  it("does not apply inactive coupon", () => {
    const items = [makeItem(100)];
    const coupon: Coupon = { id: 2, code: "OFF", discount_type: "percent", value: 50, is_active: false };
    const result = calculateCartTotals({ items, coupon });
    expect(result.discount).toBe(0);
  });

  it("applies flat-rate shipping when below free threshold", () => {
    const items = [makeItem(40)];
    const shipping: ShippingRules = { freeOver: 50, flatRate: 5 };
    const result = calculateCartTotals({ items, shippingRules: shipping });
    expect(result.shipping).toBe(5);
    expect(result.total).toBe(45);
  });

  it("applies the flat-rate shipping when free shipping is disabled", () => {
    const items = [makeItem(40)];
    const shipping: ShippingRules = { freeOver: 0, flatRate: 2 };
    const result = calculateCartTotals({ items, shippingRules: shipping });
    expect(result.shipping).toBe(2);
    expect(result.total).toBe(42);
  });

  it("gives free shipping when at or above free threshold", () => {
    const items = [makeItem(50)];
    const shipping: ShippingRules = { freeOver: 50, flatRate: 5 };
    const result = calculateCartTotals({ items, shippingRules: shipping });
    expect(result.shipping).toBe(0);
    expect(result.total).toBe(50);
  });

  it("computes tax on the discounted subtotal and adds shipping afterward", () => {
    const items = [makeItem(100)];
    const coupon = activeCoupon("fixed", 10);
    const shipping: ShippingRules = { flatRate: 10 };
    // taxable = 100 - 10 = 90, vat = 10%, then shipping is added after tax
    const result = calculateCartTotals({ items, coupon, shippingRules: shipping, taxRatePercent: 10 });
    expect(result.vat).toBeCloseTo(9);
    expect(result.total).toBeCloseTo(109);
  });
});
