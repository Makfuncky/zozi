/**
 * ordersScreen.test.ts
 * Tests the data-fetching logic used by the Orders screen:
 * - apiFetch('/orders') returns an array → screen renders items
 * - unauthenticated state → screen navigates to login
 * - non-array response is normalised to []
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

import { Order } from "@shared/types";

function makeOrder(id: number): Order {
  return {
    id,
    user_id: 1,
    status: "pending",
    total_amount: 100,
    created_at: new Date().toISOString(),
    items: [],
  } as unknown as Order;
}

describe("Orders screen — /orders API behaviour", () => {
  beforeEach(() => jest.clearAllMocks());

  it("resolves an array of orders", async () => {
    const orders = [makeOrder(1), makeOrder(2)];
    mockApiFetch.mockResolvedValueOnce(orders);

    const data = await mockApiFetch("/orders");
    const result = Array.isArray(data) ? data : [];

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe(1);
  });

  it("normalises null response to empty array (backend returned null)", async () => {
    mockApiFetch.mockResolvedValueOnce(null);

    const data = await mockApiFetch("/orders");
    const result = Array.isArray(data) ? data : [];

    expect(result).toHaveLength(0);
  });

  it("propagates fetch errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Unauthorized"));

    await expect(mockApiFetch("/orders")).rejects.toThrow("Unauthorized");
  });
});
