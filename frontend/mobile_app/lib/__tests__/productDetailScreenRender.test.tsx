import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockGetRecommendations = jest.fn();
const mockRouterPush = jest.fn();
const mockTrackRecent = jest.fn();
const mockAddItem = jest.fn();
const mockWishlistAdd = jest.fn();
const mockWishlistRemove = jest.fn();
const mockToastWarning = jest.fn();
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();

let mockProduct: any;
let mockIsLoggedIn = false;

const recentState = {
  track: (...args: unknown[]) => mockTrackRecent(...args),
  products: [] as unknown[],
};

const localeState = {
  locale: "en",
  t: (value: string) => value,
};

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "android", select: (obj: Record<string, unknown>) => obj.android ?? obj.default ?? null },
    Dimensions: { get: () => ({ width: 360, height: 800 }) },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    Image: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Image", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    StyleSheet: {
      create: (styles: unknown) => styles,
      flatten: (style: unknown) => style,
    },
    Linking: { openURL: jest.fn() },
    Share: { share: jest.fn().mockResolvedValue(undefined) },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useLocalSearchParams: () => ({ id: String(mockProduct?.id ?? 42) }),
  useRouter: () => ({ push: mockRouterPush, replace: jest.fn(), back: jest.fn() }),
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
  getRecommendations: (...args: unknown[]) => mockGetRecommendations(...args),
  resolveApiAssetUrl: (value?: string | null) => value ?? null,
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: any) => unknown) => selector({
    format: (value: number) => `AED ${Number(value).toFixed(2)}`,
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        accent: "#ff9900",
        warning: "#f59e0b",
        danger: "#dc2626",
        success: "#16a34a",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
        onBrand: "#ffffff",
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
      radius: { sm: 8, md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20, xl: 24 },
      gradients: { button: ["#7CFC00", "#32CD32"] },
    },
  }),
}));

jest.mock("@/lib/cartStore", () => ({
  useCartStore: () => ({ addItem: (...args: unknown[]) => mockAddItem(...args) }),
}));

jest.mock("@/lib/wishlistStore", () => ({
  useWishlistStore: () => ({
    has: () => false,
    add: (...args: unknown[]) => mockWishlistAdd(...args),
    remove: (...args: unknown[]) => mockWishlistRemove(...args),
  }),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({ isLoggedIn: mockIsLoggedIn }),
}));

jest.mock("@/lib/recentlyViewedStore", () => ({
  useRecentlyViewedStore: (selector: (state: any) => unknown) => selector(recentState),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: any) => unknown) => selector(localeState),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (value: string) => value,
  useTranslateTexts: (values: string[]) => values,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    row: { flexDirection: "row" },
    title: { color: "#111111" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    textBrand: { color: "#123456" },
  }),
}));

jest.mock("@/components/ui/LoadingSpinner", () => ({
  LoadingSpinner: () => React.createElement("Text", null, "loading"),
}));

jest.mock("@/components/ui/Badge", () => ({
  Badge: ({ label, ...props }: { label: string }) => React.createElement("Text", props, label),
}));

jest.mock("@/components/ui/Button", () => ({
  Button: ({ children, label, ...props }: { children?: React.ReactNode; label?: string }) => React.createElement("TouchableOpacity", props, children ?? label),
}));

jest.mock("@/components/ui/GlassCard", () => {
  const React = require("react");
  return ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children);
});

jest.mock("@/lib/toastStore", () => ({
  toast: {
    warning: (...args: unknown[]) => mockToastWarning(...args),
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
    info: jest.fn(),
  },
}));

jest.mock("@shared/localization", () => ({
  formatLocalizedDate: jest.fn(() => "2026-05-09"),
  isRtlLocale: jest.fn(() => false),
}));

const ProductDetailScreen = require("../../app/(tabs)/products/[id]").default;

function makeProduct(overrides: Record<string, unknown> = {}) {
  return {
    id: 42,
    name: "Trail Runner",
    description: "Performance shoe",
    price: 99,
    compare_price: 129,
    image_url: "https://example.test/trail-runner.jpg",
    additional_images: "[]",
    sizes: JSON.stringify(["M", "L"]),
    color: "Blue, Red",
    category: "Shoes",
    brand: "ZOZI",
    stock: 5,
    rating: 4.5,
    reviews: [],
    return_window_days: 14,
    tags: JSON.stringify(["running"]),
    ...overrides,
  };
}

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("product detail screen parity", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsLoggedIn = false;
    recentState.products = [];
    mockProduct = makeProduct();
    mockGetRecommendations.mockResolvedValue([]);
    mockApiFetch.mockImplementation(async (path: unknown) => {
      if (typeof path === "string" && path === `/products/${mockProduct.id}`) {
        return mockProduct;
      }
      if (typeof path === "string" && path.startsWith("/products?")) {
        return [];
      }
      return [];
    });
  });

  it("requires selecting a size before adding a variant product to cart", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProductDetailScreen />);
    });
    await flush();

    await act(async () => {
      await renderer.root.findByProps({ testID: "product-detail-add-to-cart" }).props.onPress();
    });

    expect(mockAddItem).not.toHaveBeenCalled();
    expect(mockToastWarning).toHaveBeenCalledWith("Please select a size");
  });

  it("adds the selected variant and routes to checkout on buy now", async () => {
    mockAddItem.mockResolvedValue(undefined);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProductDetailScreen />);
    });
    await flush();

    await act(async () => {
      renderer.root.findByProps({ testID: "product-detail-size-m" }).props.onPress();
      renderer.root.findByProps({ testID: "product-detail-color-blue" }).props.onPress();
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "product-detail-buy-now" }).props.onPress();
    });

    expect(mockAddItem).toHaveBeenCalledWith(expect.objectContaining({ id: 42 }), 1, "M", "Blue");
    expect(mockRouterPush).toHaveBeenCalledWith("/checkout");
    expect(mockToastSuccess).toHaveBeenCalledWith("Added to cart");
  });

  it("disables purchase actions when the product is out of stock", async () => {
    mockProduct = makeProduct({ stock: 0, sizes: null, color: "" });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProductDetailScreen />);
    });
    await flush();

    expect(renderer.root.findByProps({ testID: "product-detail-add-to-cart" }).props.disabled).toBe(true);
    expect(renderer.root.findByProps({ testID: "product-detail-buy-now" }).props.disabled).toBe(true);
    const stockStatus = renderer.root.findByProps({ testID: "product-detail-stock-status" });
    const stockLabel = stockStatus.findAll((node) => String(node.type) === "Text")[0];
    expect(stockLabel.props.children).toBe("outOfStock");
  });

  it("updates the active gallery dot when the gallery scroll position changes", async () => {
    mockProduct = makeProduct({
      additional_images: JSON.stringify([
        "https://example.test/trail-runner-side.jpg",
        "https://example.test/trail-runner-sole.jpg",
      ]),
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProductDetailScreen />);
    });
    await flush();

    const before = renderer.root.findByProps({ testID: "product-detail-gallery-dot-0" });
    const activeBefore = before.props.style.find((entry: { width?: number }) => entry?.width === 20);
    expect(activeBefore).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "product-detail-gallery" }).props.onMomentumScrollEnd({
        nativeEvent: { contentOffset: { x: 360 } },
      });
    });

    const after = renderer.root.findByProps({ testID: "product-detail-gallery-dot-1" });
    const activeAfter = after.props.style.find((entry: { width?: number }) => entry?.width === 20);
    expect(activeAfter).toBeTruthy();
  });

  it("routes to a recommended product when the recommendation tile is pressed", async () => {
    mockIsLoggedIn = true;
    mockGetRecommendations.mockResolvedValue([
      {
        id: 77,
        name: "Recommended Runner",
        price: 149,
        image_url: "https://example.test/recommended.jpg",
        category: { name: "Shoes" },
      },
    ]);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProductDetailScreen />);
    });
    await flush();

    const recommendationTile = renderer.root
      .findAll((node) => node.props.testID === "product-detail-recommendation-77" && String(node.type) === "TouchableOpacity")[0];

    await act(async () => {
      recommendationTile.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/(tabs)/products/77");
  });
});
