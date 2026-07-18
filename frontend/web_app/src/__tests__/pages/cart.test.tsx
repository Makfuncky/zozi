/**
 * Tests for cart page (CartPage)
 * Covers: empty state, item list render, quantity update, remove item
 */

import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockApiFetch = jest.fn();

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: true, user: null }),
}));

const mockRemoveItem = jest.fn();
const mockUpdateQuantity = jest.fn();
const mockClearCart = jest.fn();
let mockItems: any[] = [];
let mockDeliveryDetails: Record<string, unknown> = {};
let useTranslatedOutput = false;

jest.mock("@/lib/cartStore", () => ({
  useCartStore: (sel: any) =>
    sel({
      items: mockItems,
      removeItem: mockRemoveItem,
      updateQuantity: mockUpdateQuantity,
      clearCart: mockClearCart,
      getTotal: () => mockItems.reduce((s: number, i: any) => s + i.price * i.quantity, 0),
    }),
}));

jest.mock("@/lib/deliveryStore", () => ({
  useDeliveryStore: (sel: any) => sel({
    details: mockDeliveryDetails,
    initialize: jest.fn(),
    updateField: jest.fn(),
    hydrateFromAddressBook: jest.fn(),
  }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => sel({ addToast: jest.fn() }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (sel: any) => sel({ format: (p: number) => `$${p.toFixed(2)}` }),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (url: any) => url || "/placeholder.svg",
}));

jest.mock("@/lib/cartUtils", () => ({
  __esModule: true,
  default: (opts: any) => ({
    subtotal: opts.items.reduce((s: number, i: any) => s + i.price * i.quantity, 0),
    discount: 0,
    shipping: 2,
    vat: 2.75,
    total: opts.items.reduce((s: number, i: any) => s + i.price * i.quantity, 0) + 4.75,
  }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: Array<string | null | undefined>) =>
    texts.map((text) => {
      if (!text) return "";
      return useTranslatedOutput ? `AR:${text}` : text;
    }),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, layout, ...p }: any) => (
      <div {...p}>{children}</div>
    ),
  },
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
}));

jest.mock("next/image", () => function NextImageMock({ src, alt }: any) { return <img src={src} alt={alt} />; });

// ── Tests ────────────────────────────────────────────────────────────────────

import CartPage from "@/app/cart/page";

function makeItem(id: number, name: string, price = 10, quantity = 1) {
  return {
    id, name, price, quantity,
    image_url: null, category: "test", stock: 10, is_active: true,
    line_id: `${id}::::`,
  };
}

describe("CartPage — empty", () => {
  beforeEach(() => {
    mockItems = [];
    mockDeliveryDetails = {};
    useTranslatedOutput = false;
    jest.clearAllMocks();
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/config/checkout") {
        return {
          ok: true,
          json: async () => ({ vat_rate: 0.05, shipping_flat_rate: 2, free_shipping_threshold: 0 }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
  });

  it("shows empty state message when cart has no items", async () => {
    await act(async () => {
      render(<CartPage />);
    });
    expect(screen.getByText(/your cart is empty|empty/i)).toBeInTheDocument();
  });
});

describe("CartPage — with items", () => {
  beforeEach(() => {
    mockItems = [makeItem(1, "Widget", 20, 2), makeItem(2, "Gadget", 15, 1)];
    mockDeliveryDetails = {};
    useTranslatedOutput = false;
    jest.clearAllMocks();
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/config/checkout") {
        return {
          ok: true,
          json: async () => ({ vat_rate: 0.05, shipping_flat_rate: 2, free_shipping_threshold: 0 }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
  });

  it("renders cart items", async () => {
    await act(async () => {
      render(<CartPage />);
    });
    expect(screen.getByText("Widget")).toBeInTheDocument();
    expect(screen.getByText("Gadget")).toBeInTheDocument();
  });

  it("calls removeItem when remove button is clicked", async () => {
    await act(async () => {
      render(<CartPage />);
    });
    const removeBtns = screen.getAllByRole("button", { name: /remove|trash|delete/i });
    fireEvent.click(removeBtns[0]);
    expect(mockRemoveItem).toHaveBeenCalled();
  });

  it("renders translated labels when the translation hook returns localized output", async () => {
    useTranslatedOutput = true;

    await act(async () => {
      render(<CartPage />);
    });

    expect(screen.getByText("AR:Shopping Cart (2)")).toBeInTheDocument();
    expect(screen.getByText("AR:Delivery Details")).toBeInTheDocument();
    expect(screen.getByText("AR:Order Summary")).toBeInTheDocument();
    expect(screen.getByText("AR:Widget")).toBeInTheDocument();
  });

  it("shows delivery and VAT lines in the order summary", async () => {
    await act(async () => {
      render(<CartPage />);
    });

    expect(screen.getByText("Shipping")).toBeInTheDocument();
    expect(screen.getByText("VAT (5%)")).toBeInTheDocument();
  });

  it("renders selected variant labels and variant image overrides from cart rows", async () => {
    mockItems = [
      {
        ...makeItem(3, "Variant Phone", 129, 1),
        image_url: "/uploads/variant-phone-black.jpg",
        selected_size: "128 GB",
        selected_color: "Black",
        line_id: "3::128 GB::Black",
      },
    ];

    await act(async () => {
      render(<CartPage />);
    });

    expect(screen.getByText("Size: 128 GB · Color: Black")).toBeInTheDocument();
    expect(screen.getByAltText("Variant Phone")).toHaveAttribute("src", "/uploads/variant-phone-black.jpg");
  });

  it("uses approved logistics quotes in the order summary", async () => {
    mockDeliveryDetails = { country: "AE", city: "Dubai" };
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/config/checkout") {
        return {
          ok: true,
          json: async () => ({ vat_rate: 0.05, shipping_flat_rate: 2, free_shipping_threshold: 0 }),
        };
      }
      if (path === "/cart/shipping-quote") {
        return {
          ok: true,
          json: async () => ({
            shipping_amount: 7.5,
            source: "approved_logistics_partner",
            partner_name: "FastShip Logistics",
            estimated_delivery_min: 1,
            estimated_delivery_max: 3,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    await act(async () => {
      render(<CartPage />);
    });

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/cart/shipping-quote",
        expect.objectContaining({ method: "POST" }),
      );
    });

    expect(screen.getByText("Logistics rate")).toBeInTheDocument();
    expect(screen.getByText("FastShip Logistics")).toBeInTheDocument();
    expect(screen.getByText("Estimated delivery")).toBeInTheDocument();
    expect(screen.getByText("1-3 days")).toBeInTheDocument();
    expect(screen.getByText("$7.50")).toBeInTheDocument();
  });
});


