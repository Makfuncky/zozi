import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
let currentUser = { role: "admin" };

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "android", select: (options: Record<string, unknown>) => options.android ?? options.default ?? null },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    Alert: { alert: jest.fn() },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("@expo/vector-icons", () => {
  const React = require("react");
  return {
    Ionicons: ({ name, ...props }: { name: string }) => React.createElement("Ionicons", { name, ...props }),
  };
});

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        border: "#d4d4d8",
        success: "#16a34a",
        warning: "#f59e0b",
        danger: "#dc2626",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
      },
      spacing: { md: 16, sm: 12 },
      radius: { md: 12, xl: 20 },
      fontSize: { sm: 14 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({ user: currentUser }),
}));

const AdminBankAccountsScreen = require("../../app/admin/bank-accounts").default;

describe("admin bank accounts screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    currentUser = { role: "admin" };
  });

  it("shows the admin guard for non-admin users", async () => {
    currentUser = { role: "customer" };

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminBankAccountsScreen />);
    });

    expect(renderer.root.findByProps({ testID: "admin-bank-accounts-guard" })).toBeTruthy();
  });

  it("switches tabs and approves a pending bank account", async () => {
    mockApiFetch
      .mockResolvedValueOnce([
        { id: 11, entity_name: "Supplier One", bank_name: "Demo Bank", currency: "AED", verification_status: "pending", created_at: "2026-04-22T00:00:00Z" },
      ])
      .mockResolvedValueOnce([
        { id: 22, entity_name: "Partner One", bank_name: "Transit Bank", currency: "AED", verification_status: "pending", created_at: "2026-04-22T00:00:00Z" },
      ])
      .mockResolvedValueOnce({ ok: true })
      .mockResolvedValueOnce([
        { id: 22, entity_name: "Partner One", bank_name: "Transit Bank", currency: "AED", verification_status: "pending", created_at: "2026-04-22T00:00:00Z" },
      ]);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AdminBankAccountsScreen />);
    });

    expect(renderer.root.findByProps({ testID: "admin-bank-accounts-screen" })).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "admin-bank-accounts-tab-logistics_partner" }).props.onPress();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/admin/bank-accounts/pending?kind=logistics_partner");

    await act(async () => {
      renderer.root.findByProps({ testID: "admin-bank-accounts-card-toggle-22" }).props.onPress();
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "admin-bank-accounts-note-22" }).props.onChangeText("Verified after callback");
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "admin-bank-accounts-approve-22" }).props.onPress();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/admin/bank-accounts/22/verify",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ approved: true, note: "Verified after callback" }),
      }),
    );
  });
});