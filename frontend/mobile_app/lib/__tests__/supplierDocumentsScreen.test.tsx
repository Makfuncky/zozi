import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockListSupplierDocuments = jest.fn();
const mockRouterPush = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: any) => React.createElement("View", props, children),
    Text: ({ children, ...props }: any) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: any) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: any) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: any) => React.createElement("ActivityIndicator", props),
    Alert: { alert: jest.fn() },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush }),
}));

jest.mock("@expo/vector-icons", () => ({
  Ionicons: ({ name, ...props }: any) => React.createElement("Ionicons", { name, ...props }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        surface1: "#ffffff",
        surface2: "#f5f5f5",
        border: "#dddddd",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
        danger: "#cc0000",
      },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({ container: { flex: 1 } }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn(),
  listSupplierDocuments: (...args: unknown[]) => mockListSupplierDocuments(...args),
}));

import SupplierDocumentsScreen from "@/app/supplier/documents";

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

function findTouchableByLabel(renderer: TestRenderer.ReactTestRenderer, label: string) {
  return renderer.root.findAll((node) => {
    if (String(node.type) !== "TouchableOpacity") return false;
    return node.findAll((child) => String(child.type) === "Text" && flattenText(child.props.children).includes(label)).length > 0;
  })[0];
}

describe("SupplierDocumentsScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders compliance health with attention states and opens the guide", async () => {
    mockListSupplierDocuments.mockResolvedValueOnce([
      {
        id: 7,
        document_type: "trade_license",
        file_name: "Trade License 2026",
        document_name: "Trade License 2026",
        status: "rejected",
        review_note: "Upload a clearer scan",
        expires_at: "2000-01-01T00:00:00Z",
        uploaded_at: "2026-05-09T00:00:00Z",
      },
    ]);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierDocumentsScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const text = getRenderedText(renderer);
    expect(text).toContain("Compliance Health");
    expect(text).toContain("Needs attention");
    expect(text).toContain("Upload a clearer scan");
    expect(text).toContain("Rejected");

    const guideButton = findTouchableByLabel(renderer, "Guide");
    act(() => {
      guideButton.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/supplier/guide");
  });
});
