import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockRouterPush = jest.fn();
const mockRouterReplace = jest.fn();
const mockToastSuccess = jest.fn();
const mockToastError = jest.fn();
let mockLocalSearchParams: { section?: string } = {};

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    TextInput: (props: unknown) => React.createElement("TextInput", props),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush, replace: mockRouterReplace }),
  useLocalSearchParams: () => mockLocalSearchParams,
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
        warning: "#f59e0b",
      },
      spacing: { xs: 8, sm: 12, md: 16 },
      radius: { md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, md: 16, lg: 20 },
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

jest.mock("@/components/ui/Button", () => {
  const React = require("react");
  return {
    Button: ({ label, onPress, ...props }: { label: string; onPress?: () => void }) =>
      React.createElement("MockButton", { onPress, ...props }, label),
  };
});

jest.mock("@/lib/toastStore", () => ({
  toast: {
    success: (...args: unknown[]) => mockToastSuccess(...args),
    error: (...args: unknown[]) => mockToastError(...args),
  },
}));

import SupplierSupportScreen from "@/app/supplier/support";

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

describe("SupplierSupportScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalSearchParams = {};
  });

  it("loads support tickets and opens the ticket center", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/tickets") {
        return Promise.resolve([
          { id: 12, subject: "Need label correction", status: "open", priority: "high", created_at: "2026-05-01T09:00:00Z" },
        ]);
      }
      if (url === "/supplier/disputes") {
        return Promise.resolve({ data: [{ id: 9, dispute_type: "payout", priority: "normal", status: "pending", description: "Settlement mismatch" }] });
      }
      return Promise.resolve(null);
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierSupportScreen />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/tickets");
    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/disputes");
    expect(getRenderedText(renderer)).toContain("Supplier Support");
    expect(getRenderedText(renderer)).toContain("Need label correction");

    const openTicketCenter = renderer.root.findByProps({ testID: "supplier-support-open-ticket-center" });
    act(() => {
      openTicketCenter.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/tickets");
  });

  it("switches to the disputes workspace when the disputes tab is pressed", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/tickets") return Promise.resolve([]);
      if (url === "/supplier/disputes") return Promise.resolve({ data: [] });
      return Promise.resolve(null);
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierSupportScreen />);
    });
    await flush();

    const disputesTab = renderer.root.findByProps({ testID: "supplier-support-tab-disputes" });
    act(() => {
      disputesTab.props.onPress();
    });

    expect(mockRouterReplace).toHaveBeenCalledWith("/supplier/support?section=disputes");
  });
});