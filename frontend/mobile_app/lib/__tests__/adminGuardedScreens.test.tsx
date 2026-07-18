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
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
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
    Modal: ({ children, visible }: { children?: React.ReactNode; visible?: boolean }) => visible ? React.createElement("Modal", null, children) : null,
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    Switch: ({ value, onValueChange, ...props }: { value?: boolean; onValueChange?: (value: boolean) => void }) => React.createElement("Switch", { value, onValueChange, ...props }),
    StyleSheet: { create: (styles: unknown) => styles, absoluteFill: {} },
    Alert: { alert: jest.fn() },
  };
});

jest.mock("@expo/vector-icons", () => ({
  Feather: (props: any) => React.createElement("Feather", props),
}));

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("expo-file-system/legacy", () => ({
  cacheDirectory: "file:///cache/",
  documentDirectory: "file:///documents/",
  downloadAsync: jest.fn(),
}));

jest.mock("expo-sharing", () => ({
  isAvailableAsync: jest.fn().mockResolvedValue(true),
  shareAsync: jest.fn().mockResolvedValue(undefined),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    title: { color: "#111111" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    container: { flex: 1 },
  }),
}));

import { AdminBannersPanel } from "@/app/admin/banners";
import AdminEmailDashboard from "@/app/admin/email";
import AdminExportsScreen from "@/app/admin/exports";
import AdminLogisticsPartnersScreen from "@/app/admin/logistics-partners";
import AdminReturnsScreen from "@/app/admin/returns";
import AdminInvoicesScreen from "@/app/admin/invoices";
import AdminProductVerificationScreen from "@/app/admin/product-verification";

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
      textFaint: "#999999",
      danger: "#cc0000",
      success: "#00aa00",
    },
    spacing: { md: 16 },
    radius: { md: 12, lg: 16, xl: 20 },
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
  });
}

function hasAdminAccessMessage(renderer: TestRenderer.ReactTestRenderer) {
  return renderer.root.findAll((node) => {
    if (String(node.type) !== "Text") return false;
    const children = Array.isArray(node.props.children) ? node.props.children.join("") : node.props.children;
    return children === "Admin access required";
  }).length > 0;
}

describe("admin guarded mobile screens", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockThemeState.mockReturnValue(themeValue);
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("blocks banner management for sub-admin users without firing the admin banner fetch", async () => {
    setRole("sub_admin");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminBannersPanel />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads banner management for full admins", async () => {
    setRole("admin");
    mockApiFetch.mockResolvedValueOnce([]);

    await act(async () => {
      TestRenderer.create(<AdminBannersPanel />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/banners");
  });

  it("blocks email management for support users without firing campaign fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminEmailDashboard />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads email management for full admins", async () => {
    setRole("admin");
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/email/campaigns") return Promise.resolve([]);
      if (url === "/email/newsletter/subscribers/count") return Promise.resolve({ count: 0 });
      if (url === "/email/templates") return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await act(async () => {
      TestRenderer.create(<AdminEmailDashboard />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/email/campaigns");
    expect(mockApiFetch).toHaveBeenCalledWith("/email/newsletter/subscribers/count");
    expect(mockApiFetch).toHaveBeenCalledWith("/email/templates");
  });

  it("blocks exports management for support users without firing export requests", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminExportsScreen />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("blocks logistics partner management for support users without firing partner fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminLogisticsPartnersScreen />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads logistics partner management for sub-admin users", async () => {
    setRole("sub_admin");
    mockApiFetch.mockResolvedValueOnce([]);

    await act(async () => {
      TestRenderer.create(<AdminLogisticsPartnersScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/");
  });

  it("blocks returns management for sub-admin users without firing the returns fetch", async () => {
    setRole("sub_admin");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminReturnsScreen />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads returns management for support users", async () => {
    setRole("support");
    mockApiFetch.mockResolvedValueOnce([]);

    await act(async () => {
      TestRenderer.create(<AdminReturnsScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/returns/");
  });

  it("blocks invoice management for moderator users without firing invoice fetches", async () => {
    setRole("moderator");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminInvoicesScreen />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads invoice management for support users in read-only mode", async () => {
    setRole("support");
    mockApiFetch.mockResolvedValueOnce({ total: 0, page: 1, page_size: 25, total_pages: 1, items: [] });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminInvoicesScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/invoices/?page=1&page_size=25");
    expect(renderer.root.findAll((node) => String(node.type) === "Text" && node.props.children === "+ New")).toHaveLength(0);
  });

  it("blocks product verification for support users without firing verification fetches", async () => {
    setRole("support");

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminProductVerificationScreen />);
    });
    await flush();

    expect(hasAdminAccessMessage(renderer)).toBe(true);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("loads product verification for moderators", async () => {
    setRole("moderator");
    mockApiFetch.mockResolvedValueOnce({ total: 0, page: 1, page_size: 100, total_pages: 1, items: [] });

    await act(async () => {
      TestRenderer.create(<AdminProductVerificationScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/product-verifications/?page=1&page_size=100");
  });
});