import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockRouterPush = jest.fn();
const mockRouterReplace = jest.fn();
const mockClearCart = jest.fn();
const mockSetCountry = jest.fn().mockResolvedValue(undefined);
const mockOpenURL = jest.fn().mockResolvedValue(undefined);
let mockSearchParams: Record<string, string | string[] | undefined> = {};

const cartState = {
  items: [
    {
      product_id: 1,
      product_name: "Detox Ready Product",
      image_url: "",
      price: 25,
      quantity: 2,
    },
  ],
  clearCart: mockClearCart,
};

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: {
      OS: "android",
      select: (obj: Record<string, unknown>) => obj["android"] ?? obj["default"] ?? null,
    },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    KeyboardAvoidingView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("KeyboardAvoidingView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    Modal: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Modal", props, children),
    FlatList: ({ data = [], renderItem, ...props }: any) => React.createElement("FlatList", props, data.map((item: unknown, index: number) => renderItem({ item, index }))),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Linking: { openURL: mockOpenURL },
    Alert: { alert: jest.fn() },
    StyleSheet: {
      create: (styles: unknown) => styles,
      flatten: (style: unknown) => style,
    },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush, replace: mockRouterReplace, back: jest.fn() }),
  useLocalSearchParams: () => mockSearchParams,
}));

jest.mock("@expo/vector-icons", () => {
  const React = require("react");
  return {
    Ionicons: ({ name, ...props }: { name: string }) => React.createElement("Ionicons", { name, ...props }),
  };
});

jest.mock("expo-linear-gradient", () => {
  const React = require("react");
  return {
    LinearGradient: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("LinearGradient", props, children),
  };
});

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  ApiError: class ApiError extends Error {
    body?: unknown;
  },
}));

jest.mock("@/lib/cartStore", () => ({
  useCartStore: () => cartState,
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: any) => unknown) => selector({
    setCountry: mockSetCountry,
    format: (value: number) => `AED ${Number(value).toFixed(2)}`,
  }),
}));

jest.mock("@/lib/countryContext", () => ({
  useCountry: () => ({
    countryCode: "AE",
    isHydrated: true,
    setCountryCode: mockSetCountry,
    clearCountryCode: jest.fn(),
    refreshCountryCode: jest.fn().mockResolvedValue(undefined),
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        danger: "#dc2626",
        success: "#16a34a",
        warning: "#f59e0b",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
        onBrand: "#ffffff",
        gradients: { button: ["#7CFC00", "#32CD32"] },
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
      radius: { sm: 8, md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20, xl: 24 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    textBrand: { color: "#123456" },
    row: { flexDirection: "row" },
    divider: { height: 1, backgroundColor: "#d4d4d8" },
  }),
}));

jest.mock("@/components/ui/ErrorAlert", () => {
  const React = require("react");
  return ({ message }: { message: string }) => React.createElement("Text", null, message);
});

jest.mock("@/components/ui/GlassCard", () => {
  const React = require("react");
  return ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children);
});

const { ApiError } = require("@shared/api-core");
const CheckoutScreen = require("../../app/checkout").default;

function flattenText(value: unknown): string {
  if (Array.isArray(value)) return value.map(flattenText).join(" ");
  if (value == null || typeof value === "boolean") return "";
  return String(value);
}

function getRenderedText(renderer: TestRenderer.ReactTestRenderer): string {
  return renderer.root
    .findAll((node) => String(node.type) === "Text")
    .map((node) => flattenText(node.props.children))
    .join(" ");
}

describe("checkout screen testability hooks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = {};
    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (path === "/config/checkout") {
        return {
          vat_rate: 0.05,
          shipping_flat_rate: 2,
          free_shipping_threshold: 0,
        };
      }

      if (path === "/payments/methods") {
        return {
          cod: { enabled: true, label: "Cash on Delivery", detail: "Pay when your order arrives" },
          card: { enabled: true, label: "Card Payment", detail: "Hosted checkout" },
          tap: { enabled: true, label: "Tap Payments", detail: "Hosted checkout" },
          paytabs: { enabled: false, label: "PayTabs", detail: "Disabled" },
          thawani: { enabled: false, label: "Thawani Pay", detail: "Disabled" },
        };
      }

      if (path === "/orders/preview") {
        return {
          subtotal_amount: 50,
          discount_amount: 0,
          tax_amount: 2.5,
          vat_amount: 2.5,
          shipping_amount: 7.5,
          total_amount: 60,
          currency: "AED",
          payment_method: "cod",
          payment_gateway_code: null,
          payment_gateway_fee_amount: 0,
          payment_customer_total_amount: 60,
          payment_gateway_fee_passed_to_customer: false,
          country_id: 1,
          country_code: "AE",
          country_name: "United Arab Emirates",
          shipment_groups: [{ partner_name: "ZOZI Express", estimated_delivery_min: 2, estimated_delivery_max: 4 }],
          tax_breakdown: { tax_name: "VAT", country_code: "AE", currency: "AED", tax_rate: 0.05 },
        };
      }

      if (path === "/orders") {
        return { id: 91 };
      }

      if (path === "/payments/tap/create") {
        return { redirect_url: "https://tap.test/checkout" };
      }

      if (path === "/payments/stripe/create-checkout-session") {
        return { checkout_url: "https://stripe.test/checkout/session_91" };
      }

      if (path === "/payments/tap/confirm") {
        return { status: "confirmed", order_id: 91, order_status: "confirmed", charge_id: "chg_tap_91", paid_at: "2026-05-09T18:00:00Z" };
      }

      if (path === "/payments/paytabs/confirm") {
        return { status: "pending_verification", order_id: 91, order_status: "pending" };
      }

      return [];
    });
  });

  it("renders review controls then transitions into shipping and payment steps", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/config/checkout", { skipAuth: true });
    expect(mockApiFetch).toHaveBeenCalledWith("/payments/methods");

    expect(renderer.root.findByProps({ testID: "checkout-screen" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-coupon-input" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-shipping" })).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "checkout-open-address-picker" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-full-name" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-shipping-helper" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(true);

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-open-address-picker" }).props.onPress();
    });
    expect(mockApiFetch).toHaveBeenCalledWith("/users/me/addresses");

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-zip" }).props.onChangeText("00000");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/orders/preview",
      expect.objectContaining({ method: "POST" })
    );
    expect(renderer.root.findByProps({ testID: "checkout-shipping-quote" })).toBeTruthy();

    expect(renderer.root.findByProps({ testID: "checkout-shipping-ready" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(false);

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "checkout-payment-method-cod" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-payment-method-card" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-payment-method-tap" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "checkout-place-order" })).toBeTruthy();
  });

  it("starts Stripe hosted checkout from mobile", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-zip" }).props.onChangeText("00000");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-payment-method-card" }).props.onPress();
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "checkout-place-order" }).props.onPress();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/payments/stripe/create-checkout-session",
      expect.objectContaining({ method: "POST" })
    );
    expect(mockOpenURL).toHaveBeenCalledWith("https://stripe.test/checkout/session_91");
    expect(mockRouterReplace).not.toHaveBeenCalled();
    expect(mockClearCart).not.toHaveBeenCalled();
  });

  it("allows placing a COD order without a ZIP / postal code", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(false);

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.onPress();
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "checkout-place-order" }).props.onPress();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/orders",
      expect.objectContaining({ method: "POST" })
    );
    expect(mockClearCart).toHaveBeenCalled();
    expect(renderer.root.findAll((node) => node.props.children === "Order Confirmed!").length).toBeGreaterThan(0);
  });

  it("confirms Tap payment after app deep-link return", async () => {
    mockSearchParams = { tap_order_id: "91" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/payments/tap/confirm",
      expect.objectContaining({ method: "POST" })
    );
    expect(mockClearCart).toHaveBeenCalled();
    expect(() => renderer.root.findByProps({ testID: "checkout-screen" })).toThrow();
    expect(renderer.root.findAll((node) => node.props.children === "Order Confirmed!").length).toBeGreaterThan(0);
  });

  it("shows a retry message when hosted checkout returns with a cancellation flag", async () => {
    mockSearchParams = { stripe_order_id: "91", stripe_cancelled: "1" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockApiFetch).not.toHaveBeenCalledWith(
      "/payments/confirm-card-payment",
      expect.anything()
    );
    expect(mockClearCart).not.toHaveBeenCalled();
    expect(renderer.root.findByProps({ testID: "checkout-screen" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Card payment was cancelled. You can retry payment for order #91.");
  });

  it("keeps the checkout screen open when a hosted confirmation stays pending", async () => {
    mockSearchParams = { paytabs_order_id: "91" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/payments/paytabs/confirm",
      expect.objectContaining({ method: "POST" })
    );
    expect(mockClearCart).not.toHaveBeenCalled();
    expect(renderer.root.findByProps({ testID: "checkout-screen" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("pending verification for order #91");
  });

  it("shows an actionable helper when the final preview cannot be refreshed", async () => {
    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (path === "/config/checkout") {
        return {
          vat_rate: 0.05,
          shipping_flat_rate: 2,
          free_shipping_threshold: 0,
        };
      }

      if (path === "/payments/methods") {
        return {
          cod: { enabled: true, label: "Cash on Delivery", detail: "Pay when your order arrives" },
          card: { enabled: true, label: "Card Payment", detail: "Hosted checkout" },
          tap: { enabled: true, label: "Tap Payments", detail: "Hosted checkout" },
          paytabs: { enabled: false, label: "PayTabs", detail: "Disabled" },
          thawani: { enabled: false, label: "Thawani Pay", detail: "Disabled" },
        };
      }

      if (path === "/orders/preview") {
        throw new Error("preview failed");
      }

      if (path === "/users/me/addresses") {
        return [];
      }

      return [];
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-zip" }).props.onChangeText("00000");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(renderer.root.findByProps({ testID: "checkout-preview-unavailable" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("We could not refresh your final tax and shipping totals");
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(true);
  });

  it("shows the backend coupon detail when validation fails", async () => {
    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (path === "/config/checkout") {
        return {
          vat_rate: 0.05,
          shipping_flat_rate: 2,
          free_shipping_threshold: 0,
        };
      }

      if (path === "/payments/methods") {
        return {
          cod: { enabled: true, label: "Cash on Delivery", detail: "Pay when your order arrives" },
          card: { enabled: true, label: "Card Payment", detail: "Hosted checkout" },
          tap: { enabled: true, label: "Tap Payments", detail: "Hosted checkout" },
          paytabs: { enabled: false, label: "PayTabs", detail: "Disabled" },
          thawani: { enabled: false, label: "Thawani Pay", detail: "Disabled" },
        };
      }

      if (path === "/coupons/validate") {
        throw new ApiError(422, { detail: "Coupon SAVE20 is not valid for this cart." });
      }

      return [];
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-coupon-input" }).props.onChangeText("SAVE20");
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "checkout-apply-coupon" }).props.onPress();
    });

    expect(getRenderedText(renderer)).toContain("Coupon SAVE20 is not valid for this cart.");
    expect(getRenderedText(renderer)).not.toContain("Saved AED");
  });

  it("keeps payment gated while the final preview is still refreshing", async () => {
    let resolvePreview!: (value: unknown) => void;
    const previewPromise = new Promise((resolve) => {
      resolvePreview = resolve;
    });

    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (path === "/config/checkout") {
        return {
          vat_rate: 0.05,
          shipping_flat_rate: 2,
          free_shipping_threshold: 0,
        };
      }

      if (path === "/payments/methods") {
        return {
          cod: { enabled: true, label: "Cash on Delivery", detail: "Pay when your order arrives" },
          card: { enabled: true, label: "Card Payment", detail: "Hosted checkout" },
          tap: { enabled: true, label: "Tap Payments", detail: "Hosted checkout" },
          paytabs: { enabled: false, label: "PayTabs", detail: "Disabled" },
          thawani: { enabled: false, label: "Thawani Pay", detail: "Disabled" },
        };
      }

      if (path === "/orders/preview") {
        return previewPromise;
      }

      return [];
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-zip" }).props.onChangeText("00000");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(renderer.root.findByProps({ testID: "checkout-preview-loading" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Refreshing final tax and shipping totals");
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(true);

    await act(async () => {
      resolvePreview({
        subtotal_amount: 50,
        discount_amount: 0,
        tax_amount: 2.5,
        vat_amount: 2.5,
        shipping_amount: 7.5,
        total_amount: 60,
        currency: "AED",
        payment_method: "cod",
        payment_gateway_code: null,
        payment_gateway_fee_amount: 0,
        payment_customer_total_amount: 60,
        payment_gateway_fee_passed_to_customer: false,
        country_id: 1,
        country_code: "AE",
        country_name: "United Arab Emirates",
        shipment_groups: [{ partner_name: "ZOZI Express", estimated_delivery_min: 2, estimated_delivery_max: 4 }],
        tax_breakdown: { tax_name: "VAT", country_code: "AE", currency: "AED", tax_rate: 0.05 },
      });
      await Promise.resolve();
    });

    expect(() => renderer.root.findByProps({ testID: "checkout-preview-loading" })).toThrow();
    expect(renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.disabled).toBe(false);
  });

  it("surfaces backend order detail when order placement fails", async () => {
    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (path === "/config/checkout") {
        return {
          vat_rate: 0.05,
          shipping_flat_rate: 2,
          free_shipping_threshold: 0,
        };
      }

      if (path === "/payments/methods") {
        return {
          cod: { enabled: true, label: "Cash on Delivery", detail: "Pay when your order arrives" },
          card: { enabled: true, label: "Card Payment", detail: "Hosted checkout" },
          tap: { enabled: true, label: "Tap Payments", detail: "Hosted checkout" },
          paytabs: { enabled: false, label: "PayTabs", detail: "Disabled" },
          thawani: { enabled: false, label: "Thawani Pay", detail: "Disabled" },
        };
      }

      if (path === "/orders/preview") {
        return {
          subtotal_amount: 50,
          discount_amount: 0,
          tax_amount: 2.5,
          vat_amount: 2.5,
          shipping_amount: 7.5,
          total_amount: 60,
          currency: "AED",
          payment_method: "cod",
          payment_gateway_code: null,
          payment_gateway_fee_amount: 0,
          payment_customer_total_amount: 60,
          payment_gateway_fee_passed_to_customer: false,
          country_id: 1,
          country_code: "AE",
          country_name: "United Arab Emirates",
          shipment_groups: [{ partner_name: "ZOZI Express", estimated_delivery_min: 2, estimated_delivery_max: 4 }],
          tax_breakdown: { tax_name: "VAT", country_code: "AE", currency: "AED", tax_rate: 0.05 },
        };
      }

      if (path === "/orders") {
        throw new ApiError(409, { detail: "Selected payment method is unavailable for this country." });
      }

      return [];
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CheckoutScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-shipping" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-full-name" }).props.onChangeText("Customer Flow User");
      renderer.root.findByProps({ testID: "checkout-phone" }).props.onChangeText("+971500000001");
      renderer.root.findByProps({ testID: "checkout-address" }).props.onChangeText("Business Bay Street 12");
      renderer.root.findByProps({ testID: "checkout-city" }).props.onChangeText("Dubai");
      renderer.root.findByProps({ testID: "checkout-zip" }).props.onChangeText("00000");
      renderer.root.findByProps({ testID: "checkout-country" }).props.onChangeText("UAE");
    });

    await act(async () => {
      await Promise.resolve();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "checkout-continue-to-payment" }).props.onPress();
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "checkout-place-order" }).props.onPress();
    });

    expect(getRenderedText(renderer)).toContain("Selected payment method is unavailable for this country.");
    expect(mockClearCart).not.toHaveBeenCalled();
  });
});