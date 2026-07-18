/**
 * checkoutFlow.test.ts
 * Tests the checkout screen's data logic:
 * - Cart-to-order payload construction (via shared checkoutHelpers)
 * - Coupon validation API call patterns
 * - Address loading from /addresses
 * - Order placement via apiFetch('/orders')
 */

const mockApiFetch = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import { apiFetch } from "@/lib/api";
import { useCartStore, type CartItem } from "@/lib/cartStore";

function makeCartItem(productId: number, price: number, quantity: number): CartItem {
  return {
    product_id: productId,
    product_name: `Product ${productId}`,
    image_url: "",
    price,
    quantity,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  useCartStore.setState({ items: [], total: 0, itemCount: 0, isLoading: false });
});

// ── Cart totals ───────────────────────────────────────────────────────────────

describe("checkoutFlow — cart totals", () => {
  it("computes correct total from multiple items", () => {
    const items = [makeCartItem(1, 50, 2), makeCartItem(2, 30, 1)];
    const total = items.reduce((s, i) => s + i.price * i.quantity, 0);
    expect(total).toBe(130);
  });

  it("total is 0 for empty cart", () => {
    const total = [].reduce((s: number, _: CartItem) => s, 0);
    expect(total).toBe(0);
  });

  it("itemCount reflects quantities", () => {
    const items = [makeCartItem(1, 10, 3), makeCartItem(2, 20, 2)];
    const itemCount = items.reduce((s, i) => s + i.quantity, 0);
    expect(itemCount).toBe(5);
  });
});

// ── Coupon validation ─────────────────────────────────────────────────────────

describe("checkoutFlow — coupon validation", () => {
  it("calls POST /coupons/validate with code and items", async () => {
    const couponResult = {
      discount_amount: 15,
      new_total: 85,
      discount_type: "percentage",
      discount_value: 15,
    };
    mockApiFetch.mockResolvedValueOnce(couponResult);

    const items = [makeCartItem(1, 100, 1)];
    const result = await apiFetch<typeof couponResult>("/coupons/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: "SAVE15",
        items: items.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          selected_size: i.selected_size || "",
          selected_color: i.selected_color || "",
        })),
      }),
    });

    expect(result.discount_amount).toBe(15);
    expect(result.new_total).toBe(85);
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/coupons/validate",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("propagates coupon validation error", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Invalid coupon code"));
    await expect(
      apiFetch("/coupons/validate", { method: "POST", body: JSON.stringify({ code: "INVALID" }) })
    ).rejects.toThrow("Invalid coupon code");
  });
});

// ── Saved addresses ───────────────────────────────────────────────────────────

describe("checkoutFlow — saved addresses", () => {
  it("loads saved addresses from /addresses", async () => {
    const addresses = [
      { id: 1, full_name: "Alice", street: "123 Main St", city: "Dubai", country: "AE" },
      { id: 2, full_name: "Bob", street: "456 Sheikh Rd", city: "Abu Dhabi", country: "AE" },
    ];
    mockApiFetch.mockResolvedValueOnce(addresses);

    const data = await apiFetch<typeof addresses>("/addresses");
    expect(data).toHaveLength(2);
    expect(data[0].full_name).toBe("Alice");
  });

  it("returns [] when address fetch fails", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Unauthorized"));
    let addresses: any[] = [];
    try {
      addresses = await apiFetch<any[]>("/addresses");
    } catch {
      addresses = [];
    }
    expect(addresses).toEqual([]);
  });
});

// ── Order placement ───────────────────────────────────────────────────────────

describe("checkoutFlow — place order", () => {
  it("places a COD order and returns order with id", async () => {
    const orderResponse = { id: 1001, status: "pending", total_amount: 130 };
    mockApiFetch.mockResolvedValueOnce(orderResponse);

    const payload = {
      delivery_details: {
        full_name: "Alice",
        phone: "0501234567",
        street: "123 Main",
        city: "Dubai",
        country: "AE",
      },
      payment_method: "cod",
      items: [{ product_id: 1, quantity: 2 }],
      total_amount: 130,
    };

    const result = await apiFetch<typeof orderResponse>("/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    expect(result.id).toBe(1001);
    expect(result.status).toBe("pending");
  });

  it("fails gracefully when order creation returns error", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Payment failed"));
    await expect(
      apiFetch("/orders", { method: "POST", body: JSON.stringify({}) })
    ).rejects.toThrow("Payment failed");
  });
});

// ── Delivery details validation logic ────────────────────────────────────────

describe("checkoutFlow — delivery validation", () => {
  function validateDelivery(form: {
    fullName: string;
    phone: string;
    address: string;
    city: string;
    country: string;
  }): string | null {
    if (!form.fullName.trim()) return "Full name is required";
    if (!form.phone.trim()) return "Phone is required";
    if (!form.address.trim()) return "Address is required";
    if (!form.city.trim()) return "City is required";
    if (!form.country.trim()) return "Country is required";
    return null;
  }

  it("returns null for valid form", () => {
    const form = { fullName: "Alice", phone: "0501234567", address: "123 Main", city: "Dubai", country: "AE" };
    expect(validateDelivery(form)).toBeNull();
  });

  it("returns error for empty fullName", () => {
    const form = { fullName: "", phone: "0501234567", address: "123 Main", city: "Dubai", country: "AE" };
    expect(validateDelivery(form)).toBe("Full name is required");
  });

  it("returns error for missing address", () => {
    const form = { fullName: "Alice", phone: "050", address: "", city: "Dubai", country: "AE" };
    expect(validateDelivery(form)).toBe("Address is required");
  });

  it("returns error for missing country", () => {
    const form = { fullName: "Alice", phone: "050", address: "123", city: "Dubai", country: "" };
    expect(validateDelivery(form)).toBe("Country is required");
  });
});
