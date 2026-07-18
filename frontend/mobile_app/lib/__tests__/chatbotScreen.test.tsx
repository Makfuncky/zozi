import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockRouterPush = jest.fn();
const mockThemeState = jest.fn();
const mockLocaleSelector = jest.fn();
const mockCurrencySelector = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    FlatList: ({ data, renderItem }: { data?: unknown[]; renderItem?: (args: { item: unknown }) => React.ReactNode }) =>
      React.createElement(
        "FlatList",
        null,
        Array.isArray(data)
          ? data.map((item, index) => React.createElement(React.Fragment, { key: index }, renderItem ? renderItem({ item }) : null))
          : null,
      ),
    Image: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Image", props, children),
    KeyboardAvoidingView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("KeyboardAvoidingView", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Platform: { OS: "ios" },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush }),
  useLocalSearchParams: () => ({}),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  resolveApiAssetUrl: (path?: string | null) => (path ? `http://localhost:8000${path}` : null),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: { t: (key: string) => string }) => unknown) => mockLocaleSelector(selector),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (amount: number) => string }) => unknown) => mockCurrencySelector(selector),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text?: string | null) => text ?? "",
  useTranslateTexts: (texts: Array<string | null | undefined>) => texts.map((text) => text ?? ""),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

import ChatbotScreen from "@/app/chatbot";

const themeValue = {
  theme: {
    colors: {
      brand: "#123456",
      surface0: "#ffffff",
      surface1: "#f8fafc",
      border: "#dddddd",
      text: "#111111",
      textMuted: "#666666",
      textFaint: "#999999",
    },
    spacing: {
      xs: 4,
      sm: 8,
      md: 12,
      lg: 16,
    },
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      md: 18,
    },
    radius: {
      md: 8,
    },
  },
};

const translate = (key: string) => {
  const map: Record<string, string> = {
    chatbotGreeting: "Hello! How can I help?",
    chatbotTitle: "ZOZI Assistant",
    chatbotOnline: "Online",
    chatbotPlaceholder: "Ask me anything…",
    chatbotUnknownReply: "I'm not sure about that.",
    loading: "Loading",
  };
  return map[key] ?? key;
};

describe("ChatbotScreen", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(global, "setTimeout").mockImplementation(((fn: TimerHandler) => {
      if (typeof fn === "function") fn();
      return 0 as any;
    }) as typeof setTimeout);
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    mockThemeState.mockReturnValue(themeValue);
    mockLocaleSelector.mockImplementation((selector) => selector({ t: translate }));
    mockCurrencySelector.mockImplementation((selector) => selector({ format: (amount: number) => `AED ${amount.toFixed(2)}` }));
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    jest.restoreAllMocks();
  });

  it("renders prompt chips and sends follow-up prompt selections", async () => {
    mockApiFetch
      .mockResolvedValueOnce({
        reply: "These match your search.",
        intent: "product_search",
        session_id: "mobile-chat-1",
        result_mode: "exact",
        suggested_prompts: ["Only show size XL", "Show cheaper alternatives"],
        products: [
          {
            id: 12,
            name: "Nike Performance Black T-Shirt",
            price: 79,
            rating: 4.9,
            image_url: "/img.jpg",
            category: "Fashion",
            brand: "Nike",
            color: "Black",
            sizes: ["M", "L", "XL"],
          },
        ],
      })
      .mockResolvedValueOnce({
        reply: "Filtering to XL now.",
        intent: "product_search",
        session_id: "mobile-chat-1",
        result_mode: "none",
        suggested_prompts: [],
        products: [],
      })
      .mockResolvedValueOnce({ status: "recorded" });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<ChatbotScreen />);
    });

    const input = tree!.root.findAll((node) => String(node.type) === "TextInput")[0];
    await act(async () => {
      input.props.onChangeText("Nike black t-shirt in XL");
    });

    const sendButton = tree!.root.findAll((node) =>
      String(node.type) === "TouchableOpacity" &&
      node.findAll((child) => String(child.type) === "Text" && child.props.children === "Go").length > 0
    )[0];
    await act(async () => {
      await sendButton.props.onPress();
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(1, "/chatbot/message", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ message: "Nike black t-shirt in XL", session_id: undefined }),
    }));

    const promptButton = tree!.root.findAll((node) => String(node.type) === "TouchableOpacity").find((node) =>
      node.findAll((child) => String(child.type) === "Text" && child.props.children === "Only show size XL").length > 0
    );
    expect(promptButton).toBeTruthy();

    await act(async () => {
      await promptButton!.props.onPress();
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(2, "/chatbot/message", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ message: "Only show size XL", session_id: "mobile-chat-1" }),
    }));

    const productCard = tree!.root.findAll((node) => String(node.type) === "TouchableOpacity").find((node) =>
      node.findAll((child) => String(child.type) === "Text" && child.props.children === "Nike Performance Black T-Shirt").length > 0
    );
    expect(productCard).toBeTruthy();

    await act(async () => {
      productCard!.props.onPress();
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(3, "/chatbot/record-click/12", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ session_id: "mobile-chat-1" }),
    }));
    expect(mockRouterPush).toHaveBeenCalledWith("/(tabs)/products/12");
  });

  it("renders a close matches label for substitute product sets", async () => {
    mockApiFetch.mockResolvedValueOnce({
      reply: "I found close alternatives.",
      intent: "product_search",
      session_id: "mobile-close-1",
      result_mode: "close",
      suggested_prompts: [],
      products: [
        {
          id: 41,
          name: "Studio Black Bralette",
          price: 119,
          rating: 4.6,
          image_url: "/img.jpg",
          category: "Fashion",
          brand: "Studio Fit",
          color: "Black",
          sizes: ["S", "M"],
        },
      ],
    });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<ChatbotScreen />);
    });

    const input = tree!.root.findAll((node) => String(node.type) === "TextInput")[0];
    await act(async () => {
      input.props.onChangeText("show me black bra");
    });

    const sendButton = tree!.root.findAll((node) =>
      String(node.type) === "TouchableOpacity" &&
      node.findAll((child) => String(child.type) === "Text" && child.props.children === "Go").length > 0
    )[0];
    await act(async () => {
      await sendButton.props.onPress();
    });

    const label = tree!.root.findAll((node) => String(node.type) === "Text" && node.props.children === "Close matches");
    expect(label.length).toBeGreaterThan(0);
  });
});