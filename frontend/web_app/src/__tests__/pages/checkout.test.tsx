/**
 * Tests for checkout page
 * Covers: redirect when cart empty, step indicator renders, shipping validation guard
 */

import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockApiFetch = jest.fn();
const mockBuildOrderPayload = jest.fn(() => ({}));
const mockValidateDeliveryDetails = jest.fn(() => ({ valid: true }));

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: () => null }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: true, user: { id: 1, email: "user@example.com" } }),
}));

let mockCartItems: any[] = [];
const mockClearCart = jest.fn();
jest.mock("@/lib/cartStore", () => ({
  useCartStore: (sel: any) =>
    sel({
      items: mockCartItems,
      clearCart: mockClearCart,
      getTotal: () => mockCartItems.reduce((s: number, i: any) => s + i.price * i.quantity, 0),
    }),
}));

jest.mock("@/lib/deliveryStore", () => ({
  useDeliveryStore: (sel: any) =>
    sel({
      details: {
        fullName: "John Doe",
        street: "123 Main St",
        city: "Dubai",
        country: "UAE",
        zip: "00000",
      },
      initialize: jest.fn(),
      updateField: jest.fn(),
      hydrateFromAddressBook: jest.fn(),
    }),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => sel({ addToast: jest.fn() }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (sel: any) => sel({ t: (k: string) => k }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (sel: any) => sel({
    currency: { code: "AED" },
    format: (p: number) => `$${p}`,
    formatCurrent: (p: number) => `$${p}`,
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/utils", () => ({
  resolveImage: (url: any) => url || "/placeholder.svg",
}));

jest.mock("@shared/checkoutHelpers", () => ({
  validateDeliveryDetails: (...args: any[]) => (mockValidateDeliveryDetails as any)(...args),
  buildOrderPayload: (...args: any[]) => (mockBuildOrderPayload as any)(...args),
}));

jest.mock("@stripe/react-stripe-js", () => ({
  Elements: ({ children }: any) => <div data-testid="stripe-elements">{children}</div>,
  CardElement: () => <div data-testid="stripe-card-element" />,
  useStripe: () => null,
  useElements: () => null,
}));

jest.mock("@stripe/stripe-js", () => ({
  loadStripe: jest.fn(() => Promise.resolve(null)),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...p }: any) => (
      <div {...p}>{children}</div>
    ),
    h1: ({ children, ...p }: any) => (
      <h1 {...p}>{children}</h1>
    ),
  },
  AnimatePresence: function AnimatePresenceMock({ children }: any) { return <>{children}</>; },
}));

jest.mock("next/image", () => function NextImageMock({ src, alt }: any) { return <img src={src} alt={alt} />; });

// ── Tests ────────────────────────────────────────────────────────────────────

import CheckoutPage from "@/app/checkout/page";

describe("CheckoutPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockBuildOrderPayload.mockReset();
    mockBuildOrderPayload.mockReturnValue({});
    mockValidateDeliveryDetails.mockReset();
    mockValidateDeliveryDetails.mockReturnValue({ valid: true });
    mockClearCart.mockReset();
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/payments/methods") {
        return {
          ok: true,
          json: async () => ({
            cod: { enabled: true, label: "Cash on Delivery", detail: "Place the order now and pay when it arrives." },
            card: { enabled: false, label: "Credit / Debit Card", detail: "Card payments are not configured yet." },
            tap: { enabled: false, label: "Tap Payments", detail: "Tap checkout is not configured yet." },
          }),
        };
      }
      if (path === "/config/checkout") {
        return {
          ok: true,
          json: async () => ({
            vat_rate: 0.05,
            shipping_flat_rate: 2,
            free_shipping_threshold: 0,
          }),
        };
      }
      if (path === "/orders/") {
        return {
          ok: true,
          json: async () => ({
            id: 501,
            total_amount: 120,
            vat_amount: 5,
            shipping_amount: 2,
            payment_gateway_fee_amount: 0,
            payment_customer_total_amount: 120,
            payment_gateway_fee_passed_to_customer: false,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
  });

  it("shows step 1 — Review Cart — by default", async () => {
    mockCartItems = [
      { id: 1, name: "Widget", price: 50, quantity: 1, line_id: "1::::", image_url: null },
    ];
    await act(async () => {
      render(<CheckoutPage />);
    });

    expect(screen.getByText(/^Review Cart$/i)).toBeInTheDocument();
    expect(screen.getByText(/VAT \(5%\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/shipping/i).length).toBeGreaterThan(0);
  });

  it("shows the empty-cart state when cart is empty", async () => {
    mockCartItems = [];
    await act(async () => {
      render(<CheckoutPage />);
    });

    await waitFor(() => {
      expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument();
    });
  });

  it("offers cash on delivery on the payment step when card and tap are unavailable", async () => {
    mockCartItems = [
      { id: 1, name: "Widget", price: 50, quantity: 1, line_id: "1::::", image_url: null },
    ];
    await act(async () => {
      render(<CheckoutPage />);
    });

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/payments/methods");
    });

    fireEvent.click(screen.getByText(/continue to shipping/i));
    fireEvent.click(screen.getByText(/continue to payment/i));

    expect(await screen.findByText(/place the order now and pay when it arrives/i)).toBeInTheDocument();
    expect(screen.getByText(/stripe publishable and secret keys are configured/i)).toBeInTheDocument();
    expect(screen.getByText(/tap checkout is not configured yet/i)).toBeInTheDocument();
  });

  it("shows approved logistics quote details before order creation", async () => {
    mockCartItems = [
      { id: 1, name: "Widget", price: 50, quantity: 1, line_id: "1::::", image_url: null },
    ];
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/payments/methods") {
        return {
          ok: true,
          json: async () => ({
            cod: { enabled: true, label: "Cash on Delivery", detail: "Place the order now and pay when it arrives." },
            card: { enabled: false, label: "Credit / Debit Card", detail: "Card payments are not configured yet." },
            tap: { enabled: false, label: "Tap Payments", detail: "Tap checkout is not configured yet." },
          }),
        };
      }
      if (path === "/config/checkout") {
        return {
          ok: true,
          json: async () => ({
            vat_rate: 0.05,
            shipping_flat_rate: 2,
            free_shipping_threshold: 0,
          }),
        };
      }
      if (path === "/cart/shipping-quote") {
        return {
          ok: true,
          json: async () => ({
            shipping_amount: 9.5,
            source: "approved_logistics_partner",
            partner_name: "FastShip Logistics",
            estimated_delivery_min: 2,
            estimated_delivery_max: 4,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    await act(async () => {
      render(<CheckoutPage />);
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
    expect(screen.getByText("2-4 days")).toBeInTheDocument();
    expect(screen.getByText("$9.5")).toBeInTheDocument();
  });

  it("keeps selected variant choices visible in review and sends them into the checkout payload", async () => {
    mockCartItems = [
      {
        id: 1,
        name: "Widget",
        price: 59,
        quantity: 2,
        line_id: "1::128 GB::Black",
        image_url: "/uploads/widget-black.jpg",
        selected_size: "128 GB",
        selected_color: "Black",
      },
    ];

    await act(async () => {
      render(<CheckoutPage />);
    });

    expect(screen.getByText("Widget × 2 (128 GB / Black)")).toBeInTheDocument();

    fireEvent.click(screen.getByText(/continue to shipping/i));
    fireEvent.click(screen.getByText(/continue to payment/i));
    fireEvent.click(screen.getByRole("button", { name: /place cod order/i }));

    await waitFor(() => {
      expect(mockBuildOrderPayload).toHaveBeenCalledWith(
        expect.objectContaining({
          items: [
            expect.objectContaining({
              product_id: 1,
              quantity: 2,
              selected_size: "128 GB",
              selected_color: "Black",
            }),
          ],
          paymentMethod: "cod",
        })
      );
    });
    expect(mockClearCart).toHaveBeenCalled();
  });
});


