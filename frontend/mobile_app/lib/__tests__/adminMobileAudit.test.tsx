import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockAuthState = jest.fn();
const mockThemeState = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    FlatList: ({ data, renderItem, ListEmptyComponent, ListHeaderComponent, ListFooterComponent }: { data?: unknown[]; renderItem?: (args: { item: unknown; index: number }) => React.ReactNode; ListEmptyComponent?: React.ReactNode; ListHeaderComponent?: React.ReactNode; ListFooterComponent?: React.ReactNode }) =>
      React.createElement(
        "FlatList",
        null,
        ListHeaderComponent,
        Array.isArray(data) && data.length > 0
          ? data.map((item, index) => React.createElement(React.Fragment, { key: index }, renderItem ? renderItem({ item, index }) : null))
          : ListEmptyComponent,
        ListFooterComponent,
      ),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    Image: (props: unknown) => React.createElement("Image", props),
    Alert: { alert: jest.fn() },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("@expo/vector-icons", () => ({
  Feather: (props: any) => React.createElement("Feather", props),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  normalizeCollectionResponse: (data: any, keys: string[] = []) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.items)) return data.items;
    for (const key of keys) {
      if (Array.isArray(data?.[key])) return data[key];
    }
    return [];
  },
  resolveApiAssetUrl: (value: string | null | undefined) => value ?? null,
}));

jest.mock("@/lib/adminManagementUtils", () => ({
  normalizeAdminUsers: (items: any[]) => items,
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector?: (state: { locale: string }) => unknown) => {
    const state = { locale: "en" };
    return typeof selector === "function" ? selector(state) : state;
  },
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector?: (state: { format: (amount: number) => string }) => unknown) => {
    const state = { format: (amount: number) => `AED ${amount.toFixed(2)}` };
    return typeof selector === "function" ? selector(state) : state;
  },
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@shared/localization", () => ({
  formatLocalizedDate: () => "Apr 16, 2026",
  isRtlLocale: () => false,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    title: { color: "#111111" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    input: { minHeight: 44 },
  }),
}));

import AdminUsersScreen from "@/app/admin/users";
import AdminOrdersScreen from "@/app/admin/orders";
import AdminProductsScreen from "@/app/admin/products";
import AdminSuppliersScreen from "@/app/admin/suppliers";

const themeValue = {
  theme: {
    colors: {
      brand: "#123456",
      surface0: "#f8fafc",
      surface1: "#ffffff",
      surface2: "#f1f5f9",
      border: "#d4d4d8",
      text: "#111111",
      textMuted: "#666666",
    },
    spacing: { sm: 8, md: 12, lg: 16 },
    radius: { md: 12, lg: 16 },
    fontSize: { xs: 12, sm: 14, md: 16, lg: 18 },
  },
};

function setRole(role?: string | null) {
  mockAuthState.mockReturnValue({
    user: role ? { id: 1, role } : null,
  });
}

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

function findText(renderer: TestRenderer.ReactTestRenderer, text: string) {
  return renderer.root.findAll((node) => {
    if (String(node.type) !== "Text") return false;
    const children = Array.isArray(node.props.children) ? node.props.children.join("") : node.props.children;
    return children === text;
  });
}

describe("admin mobile screen audit", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockThemeState.mockReturnValue(themeValue);
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("blocks users management for support users without firing user fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminUsersScreen />);
    });
    await flush();

    expect(findText(renderer, "Admin access required")).toHaveLength(1);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads users management for sub-admin users", async () => {
    setRole("sub_admin");
    mockApiFetch.mockResolvedValueOnce({
      items: [
        {
          id: 7,
          display_name: "Alice Admin",
          username: "alice",
          email: "alice@zozi.test",
          role: "customer",
          is_active: true,
          created_at: "2026-04-16T00:00:00Z",
          total_orders: 3,
        },
      ],
    });

    await act(async () => {
      TestRenderer.create(<AdminUsersScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/users");
  });

  it("blocks products management for support users without firing product fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminProductsScreen />);
    });
    await flush();

    expect(findText(renderer, "Admin access required")).toHaveLength(1);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads products management for moderators", async () => {
    setRole("moderator");
    mockApiFetch.mockResolvedValueOnce({
      items: [
        {
          id: 9,
          name: "Desk Lamp",
          price: 19.99,
          category: "Lighting",
          stock: 4,
          supplier_id: 2,
          is_active: true,
          is_deleted: false,
          image_url: null,
        },
      ],
    });

    await act(async () => {
      TestRenderer.create(<AdminProductsScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/products");
  });

  it("blocks suppliers management for support users without firing pending-supplier fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminSuppliersScreen />);
    });
    await flush();

    expect(findText(renderer, "Admin access required")).toHaveLength(1);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads suppliers management for sub-admin users", async () => {
    setRole("sub_admin");
    mockApiFetch.mockResolvedValueOnce([
      {
        id: 4,
        email: "pending-supplier@zozi.test",
        username: "pending_supplier",
        business_name: "Pending Supplier",
      },
    ]);

    await act(async () => {
      TestRenderer.create(<AdminSuppliersScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/suppliers/pending");
  });

  it("blocks orders management for unauthenticated users without firing order fetches", async () => {
    setRole(null);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminOrdersScreen />);
    });
    await flush();

    expect(findText(renderer, "Admin access required")).toHaveLength(1);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads orders management for support users", async () => {
    setRole("support");
    mockApiFetch.mockResolvedValueOnce([
      {
        id: 11,
        user_id: 5,
        total_amount: 147.5,
        status: "pending",
        created_at: "2026-04-16T00:00:00Z",
      },
    ]);

    await act(async () => {
      TestRenderer.create(<AdminOrdersScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/orders?limit=500");
  });
});