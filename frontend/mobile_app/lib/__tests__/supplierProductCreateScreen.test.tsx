import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockRouterBack = jest.fn();
const mockToastSuccess = jest.fn();
const mockDocumentPicker = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "android", select: (options: Record<string, unknown>) => options.android ?? options.default ?? null },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    KeyboardAvoidingView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("KeyboardAvoidingView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Image: (props: unknown) => React.createElement("Image", props),
    Switch: ({ value, onValueChange, ...props }: any) => React.createElement("Switch", { value, onValueChange, ...props }),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ back: mockRouterBack }),
}));

jest.mock("@expo/vector-icons", () => {
  const React = require("react");
  return {
    Feather: ({ name, ...props }: { name: string }) => React.createElement("Feather", { name, ...props }),
  };
});

jest.mock("expo-document-picker", () => ({
  getDocumentAsync: (...args: unknown[]) => mockDocumentPicker(...args),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: any) => unknown) => selector({
    currency: { code: "AED" },
    toAED: (value: number) => value,
  }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: any) => unknown) => selector({ locale: "en" }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        border: "#d4d4d8",
        danger: "#dc2626",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
      },
      spacing: { sm: 12, md: 16 },
      radius: { md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, base: 16 },
    },
  }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    row: { flexDirection: "row" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/lib/toastStore", () => ({
  toast: { success: (...args: unknown[]) => mockToastSuccess(...args) },
}));

jest.mock("@/lib/supplierProductAi", () => ({
  hasCreateAiSource: jest.fn(() => false),
}));

jest.mock("@/lib/supplierProductForm", () => ({
  SUPPLIER_SUBCATEGORY_OPTIONS: { General: [] },
  inferSuggestedSubCategory: jest.fn(() => ""),
  mergeVariantOptions: jest.fn((_next: unknown, current: string) => current),
  normalizeSuggestedColor: jest.fn((value: string) => value),
  resolveKnownCategory: jest.fn((value: string) => value),
}));

jest.mock("@shared/supplierProductOptions", () => ({
  SUPPLIER_VARIANT_TEMPLATES: [{ key: "universal", label: "Universal", options: ["S", "M"] }],
  getSupplierVariantTemplate: jest.fn((key?: string) => ({
    key: key || "universal",
    label: "Universal",
    hint: "Choose sizes",
    options: ["S", "M"],
    customPlaceholder: "S, M",
  })),
  suggestSupplierVariantTemplate: jest.fn(() => "universal"),
}));

jest.mock("@shared/localization", () => ({
  isRtlLocale: jest.fn(() => false),
}));

jest.mock("@/components/ui/SearchableSelect", () => {
  const React = require("react");
  return {
    SearchableSelect: ({ label, value }: { label: string; value: string }) =>
      React.createElement("SearchableSelect", { label, value }),
  };
});

const NewProductScreen = require("../../app/supplier/products/new").default;

describe("supplier product create screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDocumentPicker.mockResolvedValue({ canceled: false, assets: [] });
  });

  it("shows validation error when submit is attempted without required media", async () => {
    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<NewProductScreen />);
    });

    expect(renderer.root.findByProps({ testID: "supplier-product-new-screen" })).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "supplier-product-new-submit" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "supplier-product-new-error" })).toBeTruthy();
  });

  it("submits a product after media selection and required fields are filled", async () => {
    mockDocumentPicker.mockResolvedValue({
      canceled: false,
      assets: [
        {
          uri: "file:///product.jpg",
          name: "product.jpg",
          mimeType: "image/jpeg",
        },
      ],
    });
    mockApiFetch
      .mockResolvedValueOnce({ id: 42 })
      .mockResolvedValueOnce({ ok: true });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<NewProductScreen />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "supplier-product-new-name" }).props.onChangeText("Warehouse Jacket");
      renderer.root.findByProps({ testID: "supplier-product-new-price" }).props.onChangeText("89.99");
      renderer.root.findByProps({ testID: "supplier-product-new-stock" }).props.onChangeText("12");
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "supplier-product-new-pick-media" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "supplier-product-new-main-image" })).toBeTruthy();

    await act(async () => {
      await renderer.root.findByProps({ testID: "supplier-product-new-submit" }).props.onPress();
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(
      1,
      "/supplier/products",
      expect.objectContaining({ method: "POST" }),
    );
    expect(mockApiFetch).toHaveBeenNthCalledWith(
      2,
      "/supplier/products/42/return-window",
      expect.objectContaining({ method: "PATCH" }),
    );
    expect(mockToastSuccess).toHaveBeenCalledWith("Product created!");
    expect(mockRouterBack).toHaveBeenCalled();
  });
});