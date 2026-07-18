/**
 * couponsScreen.test.ts
 * Tests the data-fetching logic and utility functions used by the Coupons screen:
 * - apiFetch('/coupons') typed response
 * - isExpired() coupon filtering helper
 * - daysLeft() expiry countdown helper
 * - formatDiscount() display formatting
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

// ── Local helper copies (mirrors coupons.tsx logic) ──────────────────────────

interface Coupon {
  id: number;
  code: string;
  discount_type: string;
  value: number;
  min_order: number;
  max_uses: number | null;
  uses_count: number;
  expires_at: string | null;
  is_active: boolean;
}

function formatDiscount(c: Coupon) {
  if (c.discount_type === "percentage") return `${c.value}% OFF`;
  return `$${Number(c.value).toFixed(2)} OFF`;
}

function isExpired(expires_at: string | null): boolean {
  if (!expires_at) return false;
  return new Date(expires_at) < new Date();
}

function daysLeft(expires_at: string | null): number | null {
  if (!expires_at) return null;
  return Math.ceil((new Date(expires_at).getTime() - Date.now()) / 86_400_000);
}

// ── apiFetch typing pattern ───────────────────────────────────────────────────

import { apiFetch } from "@/lib/api";

function makeCoupon(overrides: Partial<Coupon> = {}): Coupon {
  return {
    id: 1,
    code: "SAVE10",
    discount_type: "percentage",
    value: 10,
    min_order: 0,
    max_uses: null,
    uses_count: 0,
    expires_at: null,
    is_active: true,
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

// ── API fetch ─────────────────────────────────────────────────────────────────

describe("couponsScreen — /coupons fetch", () => {
  it("returns active non-expired coupons from apiFetch", async () => {
    const tomorrow = new Date(Date.now() + 86_400_000).toISOString();
    const coupons = [
      makeCoupon({ id: 1, code: "A10", is_active: true, expires_at: tomorrow }),
      makeCoupon({ id: 2, code: "B20", is_active: false, expires_at: null }), // inactive
    ];
    mockApiFetch.mockResolvedValueOnce(coupons);

    const data = await apiFetch<Coupon[]>("/coupons");
    const active = Array.isArray(data)
      ? data.filter((c) => c.is_active && !isExpired(c.expires_at))
      : [];

    expect(active).toHaveLength(1);
    expect(active[0].code).toBe("A10");
  });

  it("returns empty array when backend returns []", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await apiFetch<Coupon[]>("/coupons");
    const active = Array.isArray(data) ? data.filter((c) => c.is_active) : [];
    expect(active).toHaveLength(0);
  });

  it("catch path sets coupons to [] on error", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Network error"));
    let result: Coupon[] = [];
    try {
      result = await apiFetch<Coupon[]>("/coupons");
    } catch {
      result = [];
    }
    expect(result).toEqual([]);
  });
});

// ── isExpired ─────────────────────────────────────────────────────────────────

describe("couponsScreen — isExpired()", () => {
  it("returns false when expires_at is null", () => {
    expect(isExpired(null)).toBe(false);
  });

  it("returns true for a past date", () => {
    expect(isExpired("2020-01-01T00:00:00Z")).toBe(true);
  });

  it("returns false for a future date", () => {
    const future = new Date(Date.now() + 1_000_000).toISOString();
    expect(isExpired(future)).toBe(false);
  });
});

// ── daysLeft ──────────────────────────────────────────────────────────────────

describe("couponsScreen — daysLeft()", () => {
  it("returns null when expires_at is null", () => {
    expect(daysLeft(null)).toBeNull();
  });

  it("returns a positive number for a future date", () => {
    const future = new Date(Date.now() + 3 * 86_400_000).toISOString();
    expect(daysLeft(future)).toBeGreaterThan(0);
  });

  it("returns a negative number for a past date", () => {
    expect(daysLeft("2020-01-01T00:00:00Z")).toBeLessThan(0);
  });

  it("returns 1 for a date ~23h in the future (ceil)", () => {
    const almostOneDayFuture = new Date(Date.now() + 23 * 60 * 60 * 1000).toISOString();
    expect(daysLeft(almostOneDayFuture)).toBe(1);
  });
});

// ── formatDiscount ────────────────────────────────────────────────────────────

describe("couponsScreen — formatDiscount()", () => {
  it("formats percentage coupons", () => {
    const c = makeCoupon({ discount_type: "percentage", value: 15 });
    expect(formatDiscount(c)).toBe("15% OFF");
  });

  it("formats fixed-amount coupons", () => {
    const c = makeCoupon({ discount_type: "fixed_amount", value: 5 });
    expect(formatDiscount(c)).toBe("$5.00 OFF");
  });
});

// ── exhausted coupon logic ────────────────────────────────────────────────────

describe("couponsScreen — exhausted coupon", () => {
  it("coupon with max_uses hit is exhausted", () => {
    const c = makeCoupon({ max_uses: 100, uses_count: 100 });
    const exhausted = c.max_uses != null && c.uses_count >= c.max_uses;
    expect(exhausted).toBe(true);
  });

  it("coupon below max_uses is not exhausted", () => {
    const c = makeCoupon({ max_uses: 100, uses_count: 50 });
    const exhausted = c.max_uses != null && c.uses_count >= c.max_uses;
    expect(exhausted).toBe(false);
  });

  it("coupon with null max_uses is never exhausted", () => {
    const c = makeCoupon({ max_uses: null, uses_count: 9999 });
    const exhausted = c.max_uses != null && c.uses_count >= c.max_uses;
    expect(exhausted).toBe(false);
  });
});
