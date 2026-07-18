import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockDocumentPicker = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "android" },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Alert: { alert: jest.fn() },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("expo-document-picker", () => ({
  getDocumentAsync: (...args: unknown[]) => mockDocumentPicker(...args),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({ user: { id: 7, role: "supplier" } }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        border: "#d4d4d8",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
      },
      spacing: { md: 16, lg: 20 },
      radius: { lg: 16 },
      fontSize: { xs: 12, sm: 14, base: 16 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({ title: { fontSize: 18 } }),
}));

const SupplierBulkUploadScreen = require("../../app/supplier/bulk").default;

function flattenText(node: TestRenderer.ReactTestInstance | string): string {
  if (typeof node === "string") return node;
  return node.children.map((child) => flattenText(child as TestRenderer.ReactTestInstance | string)).join(" ");
}

describe("supplier bulk upload screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("uploads CSV files to the supplier import endpoint", async () => {
    mockDocumentPicker.mockResolvedValueOnce({
      canceled: false,
      assets: [{ name: "catalog.csv", uri: "file:///catalog.csv" }],
    });
    mockApiFetch.mockResolvedValueOnce({
      message: "Import completed. 2 products imported successfully.",
      imported_count: 2,
      errors: [],
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierBulkUploadScreen />);
    });

    const findPressable = (text: string) => renderer.root.find((node) => (
      typeof node.props?.onPress === "function"
      && flattenText(node).includes(text)
    ));

    await act(async () => {
      await findPressable("Select CSV File").props.onPress();
    });

    await act(async () => {
      await findPressable("Upload Products").props.onPress();
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/supplier/products/import",
      expect.objectContaining({ method: "POST" }),
    );
    expect(mockApiFetch.mock.calls[0][1].body).toBeInstanceOf(FormData);
  });
});