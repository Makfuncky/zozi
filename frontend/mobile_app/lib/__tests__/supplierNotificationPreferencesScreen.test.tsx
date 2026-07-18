import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        onBrand: "#ffffff",
        border: "#d4d4d8",
        surface0: "#ffffff",
        surface1: "#f8fafc",
        surface2: "#eef2ff",
        text: "#111111",
        textMuted: "#666666",
        info: "#0ea5e9",
        success: "#22c55e",
      },
      spacing: { xs: 8, sm: 12, md: 16 },
      radius: { lg: 16, xl: 20 },
      fontSize: { md: 16, lg: 20 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/lib/toastStore", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

import SupplierNotificationPreferencesScreen from "@/app/supplier/notification-preferences";

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("SupplierNotificationPreferencesScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads supplier notification preferences and saves a toggled setting", async () => {
    mockApiFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (url === "/supplier/notification-preferences" && !options) {
        return Promise.resolve({
          supplier_id: 5,
          notify_new_order: true,
          notify_low_stock: true,
          notify_payout_processed: true,
          notify_doc_expiry: false,
          notify_return_updates: true,
          notify_dispute_updates: true,
          in_app_enabled: true,
          email_enabled: true,
          push_enabled: false,
          updated_at: "2026-05-02T10:00:00Z",
        });
      }
      if (url === "/supplier/notification-preferences" && options?.method === "PUT") {
        return Promise.resolve({ updated_at: "2026-05-02T10:05:00Z" });
      }
      return Promise.resolve(null);
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierNotificationPreferencesScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/notification-preferences");

    const disputeToggle = renderer.root.findByProps({ testID: "supplier-pref-notify_dispute_updates" });
    await act(async () => {
      await disputeToggle.props.onPress();
    });

    expect(mockApiFetch).toHaveBeenLastCalledWith(
      "/supplier/notification-preferences",
      expect.objectContaining({
        method: "PUT",
        body: expect.stringContaining('"notify_dispute_updates":false'),
      }),
    );
    expect(mockToastSuccess).toHaveBeenCalledWith("Notification preferences saved");
  });
});