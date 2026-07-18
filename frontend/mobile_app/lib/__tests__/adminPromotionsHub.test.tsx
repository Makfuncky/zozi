import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockReplace = jest.fn();
const mockAuthState = jest.fn();
const mockThemeState = jest.fn();
let mockSection: string | undefined;

jest.mock("react-native", () => {
  const ReactLocal = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => ReactLocal.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => ReactLocal.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => ReactLocal.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => ReactLocal.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => ReactLocal.createElement("ActivityIndicator", props),
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ replace: mockReplace }),
  useLocalSearchParams: () => ({ section: mockSection }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    title: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/app/admin/banners", () => ({
  AdminBannersPanel: () => React.createElement("Text", null, "Banners panel"),
}));

jest.mock("@/app/admin/coupons", () => ({
  AdminCouponsPanel: () => React.createElement("Text", null, "Coupons panel"),
}));

jest.mock("@/app/admin/flash-sales", () => ({
  AdminFlashSalesPanel: () => React.createElement("Text", null, "Flash sales panel"),
}));

import AdminPromotionsHubScreen from "@/app/admin/promotions";

const themeValue = {
  theme: {
    colors: {
      brand: "#123456",
      surface0: "#f8fafc",
      surface1: "#ffffff",
      border: "#d4d4d8",
      text: "#111111",
      textMuted: "#666666",
      danger: "#cc0000",
    },
    spacing: { md: 16, sm: 8 },
    fontSize: { sm: 14, lg: 18 },
  },
};

function setRole(role?: string | null) {
  mockAuthState.mockReturnValue({
    user: role ? { id: 1, role } : null,
  });
}

function findText(renderer: TestRenderer.ReactTestRenderer, text: string) {
  return renderer.root.findAll((node) => {
    if (String(node.type) !== "Text") return false;
    const children = Array.isArray(node.props.children) ? node.props.children.join("") : node.props.children;
    return children === text;
  });
}

describe("admin promotions hub", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockThemeState.mockReturnValue(themeValue);
    mockSection = undefined;
  });

  it("renders the requested accessible section for admins", async () => {
    setRole("admin");
    mockSection = "banners";

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminPromotionsHubScreen />);
    });

    expect(findText(renderer, "Banners panel")).toHaveLength(1);
    expect(mockReplace).not.toHaveBeenCalledWith("/admin/login");
  });

  it("normalizes inaccessible sections to the first allowed workspace", async () => {
    setRole("sub_admin");
    mockSection = "flash-sales";

    await act(async () => {
      TestRenderer.create(<AdminPromotionsHubScreen />);
    });

    expect(mockReplace).toHaveBeenCalledWith("/admin/promotions?section=coupons");
  });
});