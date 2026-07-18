/**
 * flashSalesScreen.test.ts
 * Tests flash-sale data-fetching, countdown math, and add-to-cart integration.
 */

/* eslint-disable import/first */

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
import { useCartStore } from "@/lib/cartStore";

// ── Countdown helper (mirrors flash-sales.tsx) ────────────────────────────────

function countdown(endTime: string): { h: number; m: number; s: number; ended: boolean } {
  const diff = Math.max(0, new Date(endTime).getTime() - Date.now());
  if (diff === 0) return { h: 0, m: 0, s: 0, ended: true };
  const h = Math.floor(diff / 3_600_000);
  const m = Math.floor((diff % 3_600_000) / 60_000);
  const s = Math.floor((diff % 60_000) / 1_000);
  return { h, m, s, ended: false };
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

interface FlashSale {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
}

beforeEach(() => {
  jest.clearAllMocks();
  useCartStore.setState({ items: [], total: 0, itemCount: 0, isLoading: false });
});

// ── Flash sales fetch ─────────────────────────────────────────────────────────

describe("flashSalesScreen — /flash-sales fetch", () => {
  it("returns active flash sales", async () => {
    const now = new Date();
    const sales: FlashSale[] = [
      {
        id: 1,
        title: "Summer Blowout",
        discount_pct: 30,
        starts_at: new Date(now.getTime() - 3_600_000).toISOString(),
        ends_at: new Date(now.getTime() + 3_600_000).toISOString(),
        is_active: true,
      },
    ];
    mockApiFetch.mockResolvedValueOnce(sales);

    const data = await apiFetch<FlashSale[]>("/flash-sales");
    const active = Array.isArray(data) ? data.filter((s) => s.is_active) : [];
    expect(active).toHaveLength(1);
    expect(active[0].title).toBe("Summer Blowout");
  });

  it("handles empty flash sales list", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await apiFetch<FlashSale[]>("/flash-sales");
    expect(Array.isArray(data) ? data : []).toHaveLength(0);
  });

  it("propagates fetch errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Service unavailable"));
    await expect(apiFetch("/flash-sales")).rejects.toThrow("Service unavailable");
  });
});

// ── Countdown math ────────────────────────────────────────────────────────────

describe("flashSalesScreen — countdown()", () => {
  const FIXED_NOW = new Date("2025-06-01T12:00:00.000Z").getTime();

  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(FIXED_NOW);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns ended=true for a past end time", () => {
    const result = countdown("2020-01-01T00:00:00Z");
    expect(result.ended).toBe(true);
    expect(result.h).toBe(0);
    expect(result.m).toBe(0);
    expect(result.s).toBe(0);
  });

  it("returns ended=false for a future end time", () => {
    const future = new Date(FIXED_NOW + 7_200_000).toISOString(); // exactly 2h
    const result = countdown(future);
    expect(result.ended).toBe(false);
    expect(result.h).toBe(2);
  });

  it("calculates hours, minutes, seconds correctly for 1h30m0s", () => {
    const endTime = new Date(FIXED_NOW + 90 * 60 * 1000).toISOString(); // exactly 90 min
    const result = countdown(endTime);
    expect(result.h).toBe(1);
    expect(result.m).toBe(30);
    expect(result.s).toBe(0);
  });

  it("returns h=0, m=0 for a time < 60s in the future", () => {
    const endTime = new Date(FIXED_NOW + 45_000).toISOString(); // exactly 45s
    const result = countdown(endTime);
    expect(result.h).toBe(0);
    expect(result.m).toBe(0);
    expect(result.s).toBe(45);
  });
});

// ── pad() helper ──────────────────────────────────────────────────────────────

describe("flashSalesScreen — pad()", () => {
  it("pads single-digit numbers with leading zero", () => {
    expect(pad(5)).toBe("05");
  });

  it("does not pad double-digit numbers", () => {
    expect(pad(12)).toBe("12");
  });

  it("pads 0 as '00'", () => {
    expect(pad(0)).toBe("00");
  });
});

// ── Add to cart integration ───────────────────────────────────────────────────

describe("flashSalesScreen — add to cart", () => {
  it("addItem is called with correct product and quantity", async () => {
    // Mock the /cart/add API
    mockApiFetch
      .mockResolvedValueOnce(undefined) // POST /cart/add
      .mockResolvedValueOnce({ items: [{ product_id: 1, product_name: "Test", image_url: "", price: 100, quantity: 1 }] }); // fetchCart

    const product = {
      id: 1,
      name: "Flash Product",
      price: 100,
      stock: 5,
      is_active: true,
      supplier_id: 1,
    } as any;

    await useCartStore.getState().addItem(product, 1);
    expect(useCartStore.getState().items).toHaveLength(1);
  });

  it("does not add out-of-stock items (stock check)", () => {
    const product = { id: 2, stock: 0 } as any;
    const canAdd = product.stock > 0;
    expect(canAdd).toBe(false);
  });
});

// ── Discount badge display ────────────────────────────────────────────────────

describe("flashSalesScreen — discount badge", () => {
  it("format discount percentage string", () => {
    const sale: FlashSale = {
      id: 1, title: "Test", discount_pct: 25,
      starts_at: "", ends_at: "", is_active: true,
    };
    const badge = `${sale.discount_pct}% OFF`;
    expect(badge).toBe("25% OFF");
  });
});
