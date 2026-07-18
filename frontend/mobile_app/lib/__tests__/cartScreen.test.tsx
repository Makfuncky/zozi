import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { ApiError } from "@shared/api-core";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockRouterPush = jest.fn();
const mockUpdateQty = jest.fn();
const mockRemoveItem = jest.fn();
const mockClearCart = jest.fn();
const mockFetchCart = jest.fn();
const mockAlert = jest.fn();

const cartState: any = {
  items: [
    {
      id: 91,
      product_id: 7,
      product_name: "Falcon Speaker",
      image_url: "https://example.test/speaker.png",
      price: 199,
      quantity: 2,
      selected_size: "Standard",
      selected_color: "Black",
      available_stock: 0,
      is_available: false,
      availability_reason: "This item is out of stock. Remove it to continue.",
    },
  ],
  updateQty: (...args: unknown[]) => mockUpdateQty(...args),
  removeItem: (...args: unknown[]) => mockRemoveItem(...args),
  clearCart: () => mockClearCart(),
  fetchCart: () => mockFetchCart(),
  isLoading: false,
};

jest.mock("react-native", () => {
  const React = require("react");
  return {
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Alert: { alert: (...args: unknown[]) => mockAlert(...args) },
    Image: (props: unknown) => React.createElement("Image", props),
    ScrollView: ({ children, ...props }: any) => React.createElement("ScrollView", props, children),
    StyleSheet: { create: (styles: unknown) => styles },
    Text: ({ children, ...props }: any) => React.createElement("Text", props, children),
    TextInput: ({ children, ...props }: any) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: any) => React.createElement("TouchableOpacity", props, children),
    View: ({ children, ...props }: any) => React.createElement("View", props, children),
  };
});

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockRouterPush }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        warning: "#f59e0b",
        danger: "#dc2626",
        border: "#dddddd",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20 },
      radius: { sm: 8, md: 12, lg: 16 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20 },
    },
  }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: any) => unknown) => selector({
    formatCurrent: (value: number) => `AED ${Number(value).toFixed(2)}`,
  }),
}));

jest.mock("../cartStore", () => ({
  useCartStore: () => cartState,
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (values: string[]) => values,
}));

const CartScreen = require("../../app/cart").default;

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

describe("CartScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cartState.items = [
      {
        id: 91,
        product_id: 7,
        product_name: "Falcon Speaker",
        image_url: "https://example.test/speaker.png",
        price: 199,
        quantity: 2,
        selected_size: "Standard",
        selected_color: "Black",
        available_stock: 0,
        is_available: false,
        availability_reason: "This item is out of stock. Remove it to continue.",
      },
    ];
    cartState.isLoading = false;
  });

  it("shows an unavailable helper and blocks checkout for out-of-stock cart rows", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CartScreen />);
    });

    expect(renderer.root.findByProps({ testID: "cart-unavailable-helper" })).toBeTruthy();
    expect(renderer.root.findByProps({ testID: "cart-item-warning-91" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("This item is out of stock. Remove it to continue.");
    expect(renderer.root.findByProps({ testID: "cart-proceed-checkout" }).props.disabled).toBe(true);
    expect(renderer.root.findByProps({ testID: "cart-increment-91" }).props.disabled).toBe(true);
  });

  it("surfaces a mutation error and keeps the row quantity unchanged", async () => {
    cartState.items = [
      {
        id: 92,
        product_id: 8,
        product_name: "Travel Bag",
        image_url: "https://example.test/bag.png",
        price: 80,
        quantity: 2,
        selected_size: "M",
        selected_color: "Blue",
        available_stock: 5,
        is_available: true,
        availability_reason: null,
      },
    ];
    mockUpdateQty.mockRejectedValueOnce(new ApiError(409, { detail: "Only 1 left in stock." }));

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<CartScreen />);
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "cart-increment-92" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "cart-error-message" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Only 1 left in stock.");
    expect(renderer.root.findByProps({ testID: "cart-quantity-92" }).props.children).toBe(2);
  });
});