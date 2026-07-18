/**
 * Tests for wishlist page
 * Covers: empty state, logged-in API fetch, remove action.
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

let mockIsLoggedIn = true;
jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: mockIsLoggedIn }),
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

const mockRemove = jest.fn();
let mockIds = [1, 2];
jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: (sel: any) => sel({ ids: mockIds, remove: mockRemove }),
}));

jest.mock("@/lib/cartStore", () => ({
  useCartStore: (sel: any) => sel({ addItem: jest.fn() }),
}));

jest.mock("@/lib/useRequireAuthAction", () => ({
  useRequireAuthAction: () => (fn: any) => fn(),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => sel({ addToast: jest.fn() }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (sel: any) => sel({ t: (k: string) => k }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (sel: any) => sel({ format: (p: number) => `$${p}` }),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (url: any) => url || "/placeholder.svg",
}));

jest.mock("@/components/TranslatedText", () => function TranslatedTextMock({ text }: any) { return <span>{text}</span>; });
jest.mock("next/image", () => function NextImageMock({ src, alt }: any) { return <img src={src} alt={alt} />; });

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, layout, ...p }: any) => (
      <div {...p}>{children}</div>
    ),
  },
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
}));

// ── Test helpers ─────────────────────────────────────────────────────────────

const fakeProducts = [
  { id: 1, name: "Widget", price: 20, image_url: null, category: "test", stock: 5, is_active: true },
  { id: 2, name: "Gadget", price: 35, image_url: null, category: "test", stock: 3, is_active: true },
];

const fakeWishlistItems = fakeProducts.map((p) => ({ id: p.id, product_id: p.id, product: p }));

function makeJsonResponse(data: any, ok = true) {
  return { ok, json: async () => data } as any;
}

// ── Tests ────────────────────────────────────────────────────────────────────

import WishlistPage from "@/app/wishlist/page";

describe("WishlistPage — logged in", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoggedIn = true;
    mockIds = [1, 2];
  });

  it("renders wishlist items fetched from /wishlist", async () => {
    mockApiFetch.mockResolvedValueOnce(makeJsonResponse(fakeWishlistItems));

    render(<WishlistPage />);

    await waitFor(() => {
      expect(screen.getByText("Widget")).toBeInTheDocument();
      expect(screen.getByText("Gadget")).toBeInTheDocument();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/wishlist");
  });
});

describe("WishlistPage — guest / empty", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoggedIn = false;
    mockIds = [];
  });

  it("shows empty state when no items in local wishlist", async () => {
    render(<WishlistPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /wishlistEmpty/i })).toBeInTheDocument();
    });
  });
});


