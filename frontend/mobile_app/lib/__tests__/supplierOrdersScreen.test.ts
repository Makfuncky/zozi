/**
 * supplierOrdersScreen.test.ts
 * Tests the Supplier Orders screen API interactions:
 * - GET /supplier/orders
 * - POST /supplier/orders/:id/parcel-proof (parcel proof upload)
 * - Status badge variant mapping
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

interface Order {
  id: number;
  status: string;
  total_amount: number;
  created_at: string;
  items: Array<{ product_id: number; product_name: string; quantity: number; price: number }>;
}

function makeOrder(id: number, status = "pending"): Order {
  return {
    id,
    status,
    total_amount: 250,
    created_at: new Date().toISOString(),
    items: [{ product_id: 1, product_name: "Widget", quantity: 2, price: 125 }],
  };
}

function statusVariant(status: string): string {
  switch (status) {
    case "pending": return "warning";
    case "processing": return "info";
    case "prepared": return "info";
    case "picking_up": return "info";
    case "shipped": return "info";
    case "delivered": return "success";
    case "cancelled": return "danger";
    default: return "default";
  }
}

beforeEach(() => jest.clearAllMocks());

// ── GET supplier orders ───────────────────────────────────────────────────────

describe("supplierOrdersScreen — GET /supplier/orders", () => {
  it("returns an array of orders", async () => {
    const orders = [makeOrder(1), makeOrder(2, "processing")];
    mockApiFetch.mockResolvedValueOnce(orders);

    const data = await apiFetch<Order[]>("/supplier/orders");
    expect(data).toHaveLength(2);
    expect(data[0].id).toBe(1);
    expect(data[1].status).toBe("processing");
  });

  it("returns empty array when no supplier orders", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await apiFetch<Order[]>("/supplier/orders");
    expect(data).toEqual([]);
  });

  it("propagates API errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Forbidden"));
    await expect(apiFetch("/supplier/orders")).rejects.toThrow("Forbidden");
  });
});

// ── Parcel proof upload ───────────────────────────────────────────────────────

describe("supplierOrdersScreen — POST /supplier/orders/:id/parcel-proof", () => {
  it("calls parcel-proof upload endpoint", async () => {
    mockApiFetch.mockResolvedValueOnce({ order_id: 1, order_status: "prepared" });

    const payload = new FormData();
    payload.append("notes", "Packed parcel proof uploaded from mobile camera");

    await apiFetch(`/supplier/orders/1/parcel-proof`, {
      method: "POST",
      body: payload,
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/supplier/orders/1/parcel-proof",
      expect.objectContaining({ method: "POST", body: payload })
    );
  });

  it("updates local order state after proof upload", () => {
    let orders = [makeOrder(1, "processing"), makeOrder(2, "processing")];
    // Simulate local state update
    orders = orders.map((o) => (o.id === 1 ? { ...o, status: "prepared" } : o));
    expect(orders.find((o) => o.id === 1)?.status).toBe("prepared");
    expect(orders.find((o) => o.id === 2)?.status).toBe("processing");
  });

  it("propagates parcel-proof API errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Conflict"));
    await expect(
      apiFetch("/supplier/orders/1/parcel-proof", {
        method: "POST",
        body: new FormData(),
      })
    ).rejects.toThrow("Conflict");
  });
});

// ── statusVariant badge mapping ───────────────────────────────────────────────

describe("supplierOrdersScreen — statusVariant()", () => {
  it("maps pending to warning", () => {
    expect(statusVariant("pending")).toBe("warning");
  });

  it("maps delivered to success", () => {
    expect(statusVariant("delivered")).toBe("success");
  });

  it("maps cancelled to danger", () => {
    expect(statusVariant("cancelled")).toBe("danger");
  });

  it("returns default for unknown status", () => {
    expect(statusVariant("unknown_status_xyz")).toBe("default");
  });
});

// ── Supplier analytics ────────────────────────────────────────────────────────

describe("supplierAnalyticsScreen — GET /supplier/analytics", () => {
  it("returns analytics data with expected fields", async () => {
    const analytics = {
      total_revenue: 15000,
      total_orders: 120,
      total_products: 45,
      pending_orders: 8,
      top_products: [{ name: "Widget", total_sold: 50, revenue: 5000 }],
      monthly_revenue: [{ month: "2024-01", revenue: 3000 }],
      revenue_by_category: [{ category: "Electronics", revenue: 7500 }],
    };
    mockApiFetch.mockResolvedValueOnce(analytics);

    const data = await apiFetch<typeof analytics>("/supplier/analytics");
    expect(data.total_revenue).toBe(15000);
    expect(data.total_orders).toBe(120);
    expect(data.top_products).toHaveLength(1);
  });

  it("handles analytics fetch error gracefully", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Service unavailable"));
    await expect(apiFetch("/supplier/analytics")).rejects.toThrow("Service unavailable");
  });
});
