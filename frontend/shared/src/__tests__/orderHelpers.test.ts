import {
  normalizeOrderStatus,
  getOrderTotals,
  ORDER_STATUS_VARIANTS,
  ORDER_STATUS_LABEL,
  OrderStatusKey,
} from "../orderHelpers";
import type { Order } from "../types";

const makeOrder = (overrides: Partial<Order> = {}): Order =>
  ({
    id: 1,
    status: "pending",
    total_amount: 100,
    subtotal_amount: 80,
    vat_amount: 5,
    shipping_amount: 15,
    ...overrides,
  } as unknown as Order);

describe("normalizeOrderStatus", () => {
  it("returns 'pending' for undefined", () => {
    expect(normalizeOrderStatus(undefined)).toBe("pending");
  });

  it("lowercases a known status", () => {
    expect(normalizeOrderStatus("DELIVERED")).toBe("delivered");
    expect(normalizeOrderStatus("Shipped")).toBe("shipped");
  });

  it("returns 'pending' for unknown status string", () => {
    expect(normalizeOrderStatus("foobar")).toBe("pending");
    expect(normalizeOrderStatus("")).toBe("pending");
  });

  it("recognises all valid statuses", () => {
    const statuses: OrderStatusKey[] = ["pending", "processing", "prepared", "picking_up", "shipped", "delivered", "completed", "cancelled", "failed", "returned", "refunded"];
    statuses.forEach((s) => expect(normalizeOrderStatus(s)).toBe(s));
  });
});

describe("ORDER_STATUS_VARIANTS", () => {
  it("maps delivered to success", () => {
    expect(ORDER_STATUS_VARIANTS.delivered).toBe("success");
  });

  it("maps cancelled to danger", () => {
    expect(ORDER_STATUS_VARIANTS.cancelled).toBe("danger");
  });

  it("maps failed and returned to danger", () => {
    expect(ORDER_STATUS_VARIANTS.failed).toBe("danger");
    expect(ORDER_STATUS_VARIANTS.returned).toBe("danger");
  });

  it("maps pending to warning", () => {
    expect(ORDER_STATUS_VARIANTS.pending).toBe("warning");
  });

  it("maps processing to info", () => {
    expect(ORDER_STATUS_VARIANTS.processing).toBe("info");
  });
});

describe("ORDER_STATUS_LABEL", () => {
  it("has human-readable label for each status", () => {
    expect(ORDER_STATUS_LABEL.delivered).toBe("Delivered");
    expect(ORDER_STATUS_LABEL.cancelled).toBe("Cancelled");
    expect(ORDER_STATUS_LABEL.failed).toBe("Failed");
    expect(ORDER_STATUS_LABEL.returned).toBe("Returned");
    expect(ORDER_STATUS_LABEL.pending).toBe("Pending");
  });
});

describe("getOrderTotals", () => {
  it("returns correct breakdown when all amounts present", () => {
    const order = makeOrder({ subtotal_amount: 80, shipping_amount: 15, vat_amount: 5, total_amount: 100 });
    const totals = getOrderTotals(order);
    expect(totals.subtotal).toBe(80);
    expect(totals.shipping).toBe(15);
    expect(totals.vat).toBe(5);
    expect(totals.total).toBe(100);
  });

  it("defaults missing amounts to 0", () => {
    const order = makeOrder({ subtotal_amount: undefined, shipping_amount: undefined, vat_amount: undefined, total_amount: undefined });
    const totals = getOrderTotals(order);
    expect(totals.subtotal).toBe(0);
    expect(totals.shipping).toBe(0);
    expect(totals.vat).toBe(0);
    expect(totals.total).toBe(0);
  });

  it("falls back to subtotal+shipping+vat when total_amount is missing", () => {
    const order = makeOrder({ subtotal_amount: 80, shipping_amount: 10, vat_amount: 4, total_amount: undefined });
    const totals = getOrderTotals(order);
    expect(totals.total).toBe(94);
  });
});