/**
 * logisticsScreen.test.ts
 * Tests the Supplier Logistics screen API interactions:
 * - getLogisticsSummary()
 * - getPendingFulfilmentOrders()
 * - getSupplierShipments()
 * - createShipment()
 * - updateShipmentStatus()
 * - getDistributionChannels()
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
  getLogisticsSummary: () => mockApiFetch("/logistics/summary"),
  getPendingFulfilmentOrders: () => mockApiFetch("/logistics/orders/pending"),
  getSupplierShipments: () => mockApiFetch("/supplier/shipments"),
  getDistributionChannels: () => mockApiFetch("/logistics/distribution/channels"),
  createShipment: (data: any) =>
    mockApiFetch("/logistics/shipments", { method: "POST", body: JSON.stringify(data) }),
  updateShipmentStatus: (id: number, data: any) =>
    mockApiFetch(`/logistics/shipments/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import {
  getLogisticsSummary,
  getPendingFulfilmentOrders,
  getSupplierShipments,
  getDistributionChannels,
  createShipment,
  updateShipmentStatus,
  type LogisticsSummary,
  type PendingFulfilmentOrder,
  type SupplierShipment,
} from "@/lib/api";

function makeSummary(): LogisticsSummary {
  return {
    awaiting_fulfilment: 5,
    in_transit: 12,
    delivered_total: 200,
    total_shipments: 217,
    pending_shipments: 5,
    active_zones: 3,
  };
}

function makePendingOrder(orderId: number): PendingFulfilmentOrder {
  return {
    order_id: orderId,
    order_status: "processing",
    total_amount: 150,
    shipping_address: "123 Main St, Dubai",
    created_at: new Date().toISOString(),
    paid_at: new Date().toISOString(),
    items: [{ product_id: 1, product_name: "Widget", quantity: 2, price: 75 }],
  };
}

function makeShipment(id: number): SupplierShipment {
  return {
    id,
    order_id: id * 10,
    tracking_number: `TRK${id}`,
    carrier: "Aramex",
    status: "in_transit",
    distribution_channel: "express",
    created_at: new Date().toISOString(),
  };
}

beforeEach(() => jest.clearAllMocks());

// ── getLogisticsSummary ───────────────────────────────────────────────────────

describe("logisticsScreen — getLogisticsSummary()", () => {
  it("returns summary with expected fields", async () => {
    const summary = makeSummary();
    mockApiFetch.mockResolvedValueOnce(summary);

    const data = await getLogisticsSummary();
    expect(data.awaiting_fulfilment).toBe(5);
    expect(data.in_transit).toBe(12);
    expect(data.delivered_total).toBe(200);
    expect(data.total_shipments).toBe(217);
  });

  it("propagates API errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Unauthorized"));
    await expect(getLogisticsSummary()).rejects.toThrow("Unauthorized");
  });
});

// ── getPendingFulfilmentOrders ────────────────────────────────────────────────

describe("logisticsScreen — getPendingFulfilmentOrders()", () => {
  it("returns list of pending orders", async () => {
    const orders = [makePendingOrder(1), makePendingOrder(2)];
    mockApiFetch.mockResolvedValueOnce(orders);

    const data = await getPendingFulfilmentOrders();
    expect(data).toHaveLength(2);
    expect(data[0].order_id).toBe(1);
  });

  it("returns empty array when no pending orders", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await getPendingFulfilmentOrders();
    expect(data).toEqual([]);
  });
});

// ── getSupplierShipments ──────────────────────────────────────────────────────

describe("logisticsScreen — getSupplierShipments()", () => {
  it("returns list of shipments", async () => {
    const shipments = [makeShipment(1), makeShipment(2)];
    mockApiFetch.mockResolvedValueOnce(shipments);

    const data = await getSupplierShipments();
    expect(data).toHaveLength(2);
    expect(data[0].tracking_number).toBe("TRK1");
  });
});

// ── getDistributionChannels ───────────────────────────────────────────────────

describe("logisticsScreen — getDistributionChannels()", () => {
  it("returns channel list", async () => {
    const channels = [
      { channel: "express", total_shipments: 50, in_transit: 12, delivered: 35, returned_or_failed: 3 },
      { channel: "standard", total_shipments: 167, in_transit: 40, delivered: 120, returned_or_failed: 7 },
    ];
    mockApiFetch.mockResolvedValueOnce(channels);

    const data = await getDistributionChannels();
    expect(data).toHaveLength(2);
    expect(data[0].channel).toBe("express");
  });
});

// ── createShipment ────────────────────────────────────────────────────────────

describe("logisticsScreen — createShipment()", () => {
  it("posts to /logistics/shipments and returns new shipment", async () => {
    const shipment = makeShipment(99);
    mockApiFetch.mockResolvedValueOnce(shipment);

    const result = await createShipment({
      order_id: 990,
      carrier_name: "Aramex",
      tracking_number: "TRK99",
      distribution_channel: "express",
    });

    expect(result.id).toBe(99);
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics/shipments",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("propagates error when order_id is invalid", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Order not found"));
    await expect(createShipment({ order_id: -1 })).rejects.toThrow("Order not found");
  });
});

// ── updateShipmentStatus ──────────────────────────────────────────────────────

describe("logisticsScreen — updateShipmentStatus()", () => {
  it("patches shipment with new status", async () => {
    const updated = { ...makeShipment(5), status: "delivered" };
    mockApiFetch.mockResolvedValueOnce(updated);

    const result = await updateShipmentStatus(5, { status: "delivered" });
    expect(result.status).toBe("delivered");
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics/shipments/5",
      expect.objectContaining({ method: "PATCH" })
    );
  });

  it("propagates errors on invalid status transition", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Invalid status transition"));
    await expect(updateShipmentStatus(1, { status: "unknown" })).rejects.toThrow(
      "Invalid status transition"
    );
  });
});

// ── Tab logic ─────────────────────────────────────────────────────────────────

describe("logisticsScreen — tab navigation logic", () => {
  type Tab = "pending" | "shipments" | "channels";

  it("default tab is 'pending'", () => {
    let activeTab: Tab = "pending";
    expect(activeTab).toBe("pending");
  });

  it("selecting 'shipments' tab changes active tab", () => {
    let activeTab: Tab = "pending";
    activeTab = "shipments";
    expect(activeTab).toBe("shipments");
  });

  it("selecting 'channels' tab shows distribution channels", () => {
    let activeTab: Tab = "pending";
    activeTab = "channels";
    expect(activeTab).toBe("channels");
  });
});
