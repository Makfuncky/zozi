import {
  validateDeliveryDetails,
  buildOrderPayload,
  formatShippingAddress,
  calculateSubtotal,
  DeliveryDetails,
} from "../checkoutHelpers";

const validDetails: DeliveryDetails = {
  fullName: "Jane Doe",
  phone: "0501234567",
  street: "123 Main St",
  city: "Kuwait City",
  zip: "12345",
  country: "KW",
};

describe("validateDeliveryDetails", () => {
  it("returns valid for complete details", () => {
    expect(validateDeliveryDetails(validDetails)).toEqual({ valid: true });
  });

  it("fails when fullName is empty", () => {
    const result = validateDeliveryDetails({ ...validDetails, fullName: "" });
    expect(result.valid).toBe(false);
    expect(result.error).toBeTruthy();
  });

  it("fails when phone is missing", () => {
    const result = validateDeliveryDetails({ ...validDetails, phone: "   " });
    expect(result.valid).toBe(false);
  });

  it("fails when street is missing", () => {
    const result = validateDeliveryDetails({ ...validDetails, street: "" });
    expect(result.valid).toBe(false);
  });

  it("fails when city is missing", () => {
    const result = validateDeliveryDetails({ ...validDetails, city: "" });
    expect(result.valid).toBe(false);
  });

  it("fails when country is missing", () => {
    const result = validateDeliveryDetails({ ...validDetails, country: "" });
    expect(result.valid).toBe(false);
  });

  it("fails when zip is fewer than 3 chars", () => {
    const result = validateDeliveryDetails({ ...validDetails, zip: "AB" });
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/ZIP/i);
  });

  it("passes with zip of exactly 3 chars", () => {
    const result = validateDeliveryDetails({ ...validDetails, zip: "ABC" });
    expect(result.valid).toBe(true);
  });
});

describe("formatShippingAddress", () => {
  it("joins required fields with comma", () => {
    const result = formatShippingAddress(validDetails);
    expect(result).toContain("Jane Doe");
    expect(result).toContain("123 Main St");
    expect(result).toContain("Kuwait City");
    expect(result).toContain("12345");
    expect(result).toContain("KW");
  });
});

describe("buildOrderPayload", () => {
  const items = [{ product_id: 1, quantity: 2 }];

  it("includes required fields", () => {
    const payload = buildOrderPayload({ items, deliveryDetails: validDetails });
    expect(payload.items).toHaveLength(1);
    expect(payload.full_name).toBe("Jane Doe");
    expect(payload.shipping_address).toBeTruthy();
    expect(payload.payment_method).toBe("cod");
  });

  it("includes coupon_code when provided", () => {
    const payload = buildOrderPayload({ items, deliveryDetails: validDetails, couponCode: "SAVE10" });
    expect(payload.coupon_code).toBe("SAVE10");
  });

  it("omits coupon_code when not provided", () => {
    const payload = buildOrderPayload({ items, deliveryDetails: validDetails });
    expect(Object.prototype.hasOwnProperty.call(payload, "coupon_code")).toBe(false);
  });

  it("uses provided payment method", () => {
    const payload = buildOrderPayload({ items, deliveryDetails: validDetails, paymentMethod: "card" });
    expect(payload.payment_method).toBe("card");
  });

  it("strips undefined fields from payload", () => {
    const payload = buildOrderPayload({ items, deliveryDetails: validDetails });
    const hasUndefined = Object.values(payload).some((v) => v === undefined);
    expect(hasUndefined).toBe(false);
  });

  it("maps item fields correctly", () => {
    const richItems = [{ product_id: 42, quantity: 3, selected_size: "M", selected_color: "Blue" }];
    const payload = buildOrderPayload({ items: richItems, deliveryDetails: validDetails });
    const mappedItem = (payload.items as any[])[0];
    expect(mappedItem.product_id).toBe(42);
    expect(mappedItem.quantity).toBe(3);
    expect(mappedItem.selected_size).toBe("M");
    expect(mappedItem.selected_color).toBe("Blue");
  });
});

describe("calculateSubtotal", () => {
  it("returns 0 for empty items", () => {
    expect(calculateSubtotal([])).toBe(0);
  });

  it("sums price × quantity", () => {
    expect(calculateSubtotal([{ price: 10, quantity: 2 }, { price: 5, quantity: 3 }])).toBeCloseTo(35);
  });
});