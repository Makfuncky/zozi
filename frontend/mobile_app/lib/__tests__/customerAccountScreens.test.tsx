import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockGetReferralDashboard = jest.fn();
const mockClaimReferralShareBonus = jest.fn();
const mockRouterPush = jest.fn();
const mockRouterReplace = jest.fn();
const mockLogout = jest.fn().mockResolvedValue(undefined);

let currentAuthState = {
  user: { id: 1, username: "zozi-user", email: "user@zozi.test", role: "customer" },
  isLoggedIn: true,
  logout: mockLogout,
};

jest.mock("react-native", () => {
  const React = require("react");
  const noop = () => null;
  const AnimatedValue = jest.fn().mockImplementation(() => ({
    setValue: jest.fn(),
    interpolate: jest.fn(() => ({})),
    addListener: jest.fn(),
    removeAllListeners: jest.fn(),
  }));
  const Animated = {
    View: noop,
    Text: noop,
    Image: noop,
    Value: AnimatedValue,
    timing: jest.fn(() => ({ start: jest.fn() })),
    loop: jest.fn(() => ({ start: jest.fn(), stop: jest.fn() })),
    sequence: jest.fn(() => ({ start: jest.fn() })),
    createAnimatedComponent: (comp: unknown): unknown => comp,
    event: jest.fn(),
  };
  return {
    Platform: {
      OS: "android",
      select: (obj: Record<string, unknown>) => obj["android"] ?? obj["default"] ?? null,
    },
    Animated,
    useColorScheme: jest.fn(() => "dark"),
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    Image: (props: unknown) => React.createElement("Image", props),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    FlatList: ({ data = [], renderItem, ListEmptyComponent, ListHeaderComponent, refreshControl, ...props }: any) =>
      React.createElement(
        "FlatList",
        props,
        ListHeaderComponent ?? null,
        data.length === 0 ? ListEmptyComponent ?? null : data.map((item: unknown, index: number) => renderItem({ item, index })),
        refreshControl ?? null,
      ),
    StyleSheet: {
      create: (styles: unknown) => styles,
      flatten: (style: unknown) => style,
    },
    Alert: { alert: jest.fn() },
    Dimensions: { get: () => ({ width: 375, height: 812 }) },
  };
});

jest.mock("expo-router", () => {
  // IMPORTANT: return stable object references to prevent infinite useCallback/useEffect loops
  const stableRouter = { push: mockRouterPush, replace: mockRouterReplace, back: jest.fn() };
  return {
    Stack: { Screen: () => null },
    useRouter: () => stableRouter,
    useLocalSearchParams: () => ({}),
  };
});

jest.mock("@expo/vector-icons", () => {
  const React = require("react");
  return {
    Ionicons: ({ name, ...props }: { name: string }) => React.createElement("Ionicons", { name, ...props }),
  };
});

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  getReferralDashboard: (...args: unknown[]) => mockGetReferralDashboard(...args),
  claimReferralShareBonus: (...args: unknown[]) => mockClaimReferralShareBonus(...args),
  buildAppReferralLink: (code: string) => `zozi://signup?ref=${encodeURIComponent(code)}`,
  getOrdersPage: jest.fn().mockResolvedValue({ items: [], hasMore: false, total: 0 }),
  getMe: jest.fn().mockResolvedValue(null),
  getUserProfile: jest.fn().mockResolvedValue(null),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => currentAuthState,
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        danger: "#dc2626",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
      },
      spacing: { xs: 8, sm: 12, md: 16, lg: 20, xl: 24 },
      radius: { sm: 8, md: 12, lg: 16 },
      fontSize: { xs: 12, sm: 14, md: 16, base: 16, lg: 20, xl: 24 },
    },
    mode: "light",
    toggle: jest.fn(),
  }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector?: (state: { t: (key: string) => string }) => unknown) => {
    const state = { t: (key: string) => `T:${key}` };
    return selector ? selector(state) : state;
  },
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: Array<string | null | undefined>) => texts.map((text) => (text ? `AR:${text}` : "")),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    title: { color: "#111111" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/components/ui/EmptyState", () => {
  const React = require("react");
  return {
    EmptyState: ({ title, subtitle, action }: { title?: string; subtitle?: string; action?: { label?: string; onPress?: () => void } }) =>
      React.createElement(
        "View",
        null,
        title ? React.createElement("Text", null, title) : null,
        subtitle ? React.createElement("Text", null, subtitle) : null,
        action?.label ? React.createElement("TouchableOpacity", { onPress: action.onPress }, React.createElement("Text", null, action.label)) : null,
      ),
  };
});

jest.mock("@/components/OrderCard", () => {
  const React = require("react");
  return {
    OrderCard: ({ order }: { order: { id: number } }) => React.createElement("Text", null, `Order #${order.id}`),
  };
});

jest.mock("@/components/ui/LoadingSpinner", () => ({
  LoadingSpinner: () => null,
}));

// Mock LoadingSkeleton (orders.tsx uses relative "../components/ui/LoadingSkeleton")
jest.mock("../../components/ui/LoadingSkeleton", () => ({
  Skeleton: () => null,
  SkeletonRow: () => null,
  ProductCardSkeleton: () => null,
  ProductGridSkeleton: () => null,
}));

const ProfileScreen = require("../../app/(tabs)/profile").default;
const OrdersScreen = require("../../app/(tabs)/orders/index").default;

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

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("mobile customer account localization", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetReferralDashboard.mockResolvedValue({
      referral_code: "ZOZI1234",
      referral_link: "https://zozi.app/r/ZOZI1234",
      total_points: 0,
      referral_points: 0,
      sharing_points: 0,
      referred_count: 0,
      recent_activity: [],
    });
    mockClaimReferralShareBonus.mockResolvedValue({
      awarded_points: 0,
      total_points: 0,
      referral_points: 0,
      sharing_points: 0,
      message: "No bonus awarded",
    });
    currentAuthState = {
      user: { id: 1, username: "zozi-user", email: "user@zozi.test", role: "customer" },
      isLoggedIn: true,
      logout: mockLogout,
    };
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renders translated profile labels for customer account surfaces", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/orders/") {
        return Promise.resolve([
          { id: 1, status: "pending" },
          { id: 2, status: "delivered" },
        ]);
      }
      return Promise.resolve([]);
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<ProfileScreen />);
    });
    await flush();

    const text = getRenderedText(renderer);
    expect(text).toContain("AR:My Orders");
    expect(text).toContain("AR:Support Tickets");
    expect(text).toContain("AR:Sign Out");
  });

  it("renders translated empty orders state", async () => {
    mockApiFetch.mockResolvedValue([]);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<OrdersScreen />);
    });
    await flush();

    const text = getRenderedText(renderer);
    expect(text).toContain("AR:No orders yet");
    expect(text).toContain("AR:Start shopping to see your orders here.");
    expect(text).toContain("AR:Shop Now");
  }, 30000);
});