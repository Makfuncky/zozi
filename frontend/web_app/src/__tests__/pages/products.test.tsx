/**
 * Tests for products listing page
 * Covers: product grid render, category filter buttons present, search input
 */

import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockGet = jest.fn((_key: string): string | null => null);
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockSearchParams = { get: mockGet };
let paramValues: Record<string, string | null> = {};

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

jest.mock("next/image", () => ({
  __esModule: true,
  default: ({ src, alt }: any) => <img src={src} alt={alt} />,
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (sel: any) => sel({ t: (k: string) => k }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => sel({ addToast: jest.fn() }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (sel: any) =>
    sel({ currency: "USD", format: (p: number) => `$${p}`, formatCurrent: (p: number) => `$${p}`, toAED: (p: number) => p }),
}));

jest.mock("@/components/ProductCard", () => function ProductCardMock({ product }: any) {
  return <div data-testid="product-card">{product.name}</div>;
});

jest.mock("@/components/LoadingSkeleton", () => ({
  ProductCardSkeleton: () => <div data-testid="skeleton" />,
}));

jest.mock("@/components/SeasonalBanner", () => function SeasonalBannerMock() { return null; });
jest.mock("@/components/BrandLoading", () => function BrandLoadingMock({ label }: any) { return <div>{label}</div>; });

jest.mock("@shared/productQuery", () => ({
  buildProductQueryParams: (_opts: any) => new URLSearchParams(),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...p }: any) => (
      <div {...p}>{children}</div>
    ),
    button: ({ children, ...p }: any) => (
      <button {...p}>{children}</button>
    ),
    span: ({ children, ...p }: any) => (
      <span {...p}>{children}</span>
    ),
    ul: ({ children, ...p }: any) => (
      <ul {...p}>{children}</ul>
    ),
    li: ({ children, ...p }: any) => (
      <li {...p}>{children}</li>
    ),
  },
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
}));

const fakeProducts = [
  { id: 1, name: "Widget A", price: 10, category: "electronics", stock: 5, is_active: true, image_url: null, description: "" },
  { id: 2, name: "Widget B", price: 20, category: "fashion", stock: 3, is_active: true, image_url: null, description: "" },
];

let lastIntersectionObserverCallback: IntersectionObserverCallback | null = null;

class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin = "0px";
  readonly thresholds: ReadonlyArray<number> = [0];

  constructor(callback: IntersectionObserverCallback) {
    lastIntersectionObserverCallback = callback;
  }

  disconnect = jest.fn();
  observe = jest.fn();
  takeRecords = jest.fn(() => []);
  unobserve = jest.fn();
}

function triggerIntersection(isIntersecting = true) {
  if (!lastIntersectionObserverCallback) return;
  const entry = {
    isIntersecting,
    target: document.createElement("div"),
    intersectionRatio: isIntersecting ? 1 : 0,
    boundingClientRect: {} as DOMRectReadOnly,
    intersectionRect: {} as DOMRectReadOnly,
    rootBounds: null,
    time: Date.now(),
  } as IntersectionObserverEntry;

  lastIntersectionObserverCallback([entry], {} as IntersectionObserver);
}

// ── Tests ────────────────────────────────────────────────────────────────────

import ProductsPage from "@/app/products/page";

describe("ProductsPage", () => {
  beforeAll(() => {
    (globalThis as any).IntersectionObserver = MockIntersectionObserver;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    lastIntersectionObserverCallback = null;
    paramValues = {};
    mockGet.mockImplementation((key: string) => paramValues[key] ?? null);
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/products/autocomplete?q=")) {
        return Promise.resolve({ ok: true, json: async () => ["Dream Mart"] });
      }
      if (path === "/products/suppliers") {
        return Promise.resolve({ ok: true, json: async () => ["Supplier A"] });
      }
      if (path === "/suppliers/resolve/Dream%20Mart") {
        return Promise.resolve({ ok: true, json: async () => ({ id: 7, slug: "dream-mart", canonical_path: "/supplier=dream-mart" }) });
      }
      if (path.includes("/suppliers?limit=6") || path.includes("/suppliers?limit=4")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [{ id: 7, username: "dream_mart", business_name: "Dream Mart", slug: "dream-mart", badge_level: "verified", verification_status: "approved", credibility_score: 60, is_verified: true, product_count: 4, avg_rating: 4.8, total_reviews: 12, total_sales: 18, member_since: "2026-01-01T00:00:00" }], total: 1 }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => fakeProducts,
        headers: { get: (name: string) => (name.toLowerCase() === "x-total-count" ? "2" : null) },
      });
    });
  });

  it("renders product cards after fetch", async () => {
    render(<ProductsPage />);

    expect((await screen.findAllByTestId("product-card")).length).toBeGreaterThan(0);
  });

  it("shows the search input", async () => {
    render(<ProductsPage />);
    await screen.findAllByTestId("product-card");
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  it("shows category filter controls", async () => {
    render(<ProductsPage />);
    await screen.findAllByTestId("product-card");
    expect(screen.getByRole("button", { name: /categoriesLabel/i })).toBeInTheDocument();
  });

  it("redirects single supplier filter URLs to the supplier storefront", async () => {
    paramValues = { supplier: "Dream Mart" };

    render(<ProductsPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/supplier=dream-mart", { scroll: false });
    });
  });

  it("opens the supplier storefront when search resolves to an exact supplier", async () => {
    render(<ProductsPage />);
    await screen.findAllByTestId("product-card");

    fireEvent.change(screen.getByPlaceholderText(/search/i), { target: { value: "Dream Mart" } });
    fireEvent.click(screen.getByRole("button", { name: /searchbutton/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/supplier=dream-mart");
    });
  });

  it("auto-loads more products when the scroll sentinel enters view", async () => {
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/products/autocomplete?q=")) {
        return Promise.resolve({ ok: true, json: async () => ["Dream Mart"] });
      }
      if (path.includes("/suppliers?limit=6") || path.includes("/suppliers?limit=4")) {
        return Promise.resolve({ ok: true, json: async () => ({ items: [], total: 0 }) });
      }
      if (path.includes("offset=2")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { id: 3, name: "Widget C", price: 30, category: "electronics", stock: 4, is_active: true, image_url: null, description: "" },
            { id: 4, name: "Widget D", price: 40, category: "fashion", stock: 2, is_active: true, image_url: null, description: "" },
          ],
          headers: { get: (name: string) => (name.toLowerCase() === "x-total-count" ? "40" : null) },
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => fakeProducts,
        headers: { get: (name: string) => (name.toLowerCase() === "x-total-count" ? "40" : null) },
      });
    });

    render(<ProductsPage />);
    await screen.findAllByTestId("product-card");

    await act(async () => {
      triggerIntersection(true);
    });

    await waitFor(() => {
      expect(
        mockApiFetch.mock.calls.some((call) =>
          typeof call[0] === "string" && call[0].includes("/products?limit=24&offset=2")
        )
      ).toBe(true);
    });
  });
});


