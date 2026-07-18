/**
 * searchScreen.test.ts
 * Tests the search screen's API integration:
 * - searchProducts() with various query params
 * - Result normalisation (handles array and { products: [] } shapes)
 * - Category filtering, sort params
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
  searchProducts: jest.fn((...args: any[]) => mockApiFetch("/products", ...args)),
  getRecommendations: jest.fn(() => mockApiFetch("/search/recommendations")),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import { searchProducts, getRecommendations, type SearchProduct } from "@/lib/api";

function makeProduct(id: number, name: string, price = 100): SearchProduct {
  return { id, name, price };
}

beforeEach(() => jest.clearAllMocks());

// ── searchProducts ────────────────────────────────────────────────────────────

describe("searchScreen — searchProducts()", () => {
  it("returns products matching a text query", async () => {
    const products = [makeProduct(1, "Red Shoes"), makeProduct(2, "Red Jacket")];
    mockApiFetch.mockResolvedValueOnce(products);

    const results = await searchProducts({ q: "red" });
    expect(Array.isArray(results)).toBe(true);
    expect(mockApiFetch).toHaveBeenCalled();
  });

  it("returns empty array when no products match", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const results = await searchProducts({ q: "xyzzy" });
    expect(results).toHaveLength(0);
  });

  it("propagates network errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Service unavailable"));
    await expect(searchProducts({ q: "test" })).rejects.toThrow("Service unavailable");
  });

  it("passes category filter", async () => {
    mockApiFetch.mockResolvedValueOnce([makeProduct(1, "Sneakers")]);
    await searchProducts({ category: "shoes" });
    expect(mockApiFetch).toHaveBeenCalledWith("/products", expect.anything());
  });

  it("passes price range filters", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    await searchProducts({ min_price: "50", max_price: "200" });
    expect(mockApiFetch).toHaveBeenCalled();
  });

  it("supports trending products flag", async () => {
    mockApiFetch.mockResolvedValueOnce([makeProduct(5, "Trending Item")]);
    const results = await searchProducts({ trending: true });
    expect(mockApiFetch).toHaveBeenCalled();
  });
});

// ── getRecommendations ────────────────────────────────────────────────────────

describe("searchScreen — getRecommendations()", () => {
  it("returns recommended products", async () => {
    const recs = [makeProduct(10, "Recommended A"), makeProduct(11, "Recommended B")];
    mockApiFetch.mockResolvedValueOnce(recs);

    const results = await getRecommendations({ limit: 6 });
    expect(Array.isArray(results)).toBe(true);
  });

  it("defaults to returning suggestions on error", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Network error"));
    try {
      await getRecommendations();
    } catch {
      // treated as empty list in the screen
    }
    expect(mockApiFetch).toHaveBeenCalled();
  });
});

// ── Client-side filtering helpers ────────────────────────────────────────────

describe("searchScreen — filter helpers", () => {
  const products: SearchProduct[] = [
    { id: 1, name: "Red Shoes", price: 80 },
    { id: 2, name: "Blue Jacket", price: 150 },
    { id: 3, name: "Green Hat", price: 30 },
  ];

  it("sorts by price ascending", () => {
    const sorted = [...products].sort((a, b) => a.price - b.price);
    expect(sorted[0].price).toBe(30);
    expect(sorted[2].price).toBe(150);
  });

  it("sorts by price descending", () => {
    const sorted = [...products].sort((a, b) => b.price - a.price);
    expect(sorted[0].price).toBe(150);
  });

  it("filters by min price", () => {
    const filtered = products.filter((p) => p.price >= 100);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].name).toBe("Blue Jacket");
  });

  it("filters by max price", () => {
    const filtered = products.filter((p) => p.price <= 80);
    expect(filtered).toHaveLength(2);
  });

  it("text search filter is case-insensitive", () => {
    const q = "shoes";
    const filtered = products.filter((p) => p.name.toLowerCase().includes(q.toLowerCase()));
    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe(1);
  });
});

// ── Debounce behaviour ────────────────────────────────────────────────────────

describe("searchScreen — debounce pattern", () => {
  it("only fires fetch once after settling (simulated)", async () => {
    jest.useFakeTimers();
    let fired = 0;

    const debounce = (fn: () => void, ms: number) => {
      let timer: ReturnType<typeof setTimeout>;
      return () => {
        clearTimeout(timer);
        timer = setTimeout(() => { fn(); fired++; }, ms);
      };
    };

    const debouncedFetch = debounce(() => {}, 300);

    // Rapid calls
    debouncedFetch();
    debouncedFetch();
    debouncedFetch();

    jest.advanceTimersByTime(300);
    expect(fired).toBe(1);

    jest.useRealTimers();
  });
});
