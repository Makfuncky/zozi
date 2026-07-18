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

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => mockAuthState(),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => mockThemeState(),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    title: { color: "#111111" },
  }),
}));

import AdminAnalyticsScreen from "@/app/admin/analytics";

const themeValue = {
  theme: {
    colors: {
      brand: "#123456",
      surface0: "#ffffff",
      surface1: "#f8fafc",
      surface2: "#eef2f7",
      border: "#dddddd",
      text: "#111111",
      textMuted: "#666666",
    },
    spacing: {
      sm: 8,
      md: 12,
      lg: 16,
    },
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 20,
    },
  },
};

describe("AdminAnalyticsScreen", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    mockThemeState.mockReturnValue(themeValue);
    mockAuthState.mockReturnValue({ user: { id: 1, role: "admin" } });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("loads and renders the chatbot demand section alongside platform analytics", async () => {
    mockApiFetch
      .mockResolvedValueOnce({
        total_revenue: 5000,
        total_orders: 32,
        total_users: 120,
        total_products: 48,
        pending_orders: 5,
        active_suppliers: 9,
        revenue_today: 300,
        orders_today: 4,
        top_products: [{ name: "Laptop Stand", sales_count: 15, revenue: 900 }],
        revenue_by_day: [{ date: "2026-03-29", revenue: 300 }],
      })
      .mockResolvedValueOnce({
        total_queries: 18,
        total_clicks: 6,
        click_through_rate: 33.3,
        avg_results_per_query: 3.4,
        top_queries: [{ query: "nike black t-shirt in xl", count: 5 }],
        top_clicked_products: [{ id: 44, name: "Nike Performance Black T-Shirt", clicks: 4 }],
      });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<AdminAnalyticsScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(1, "/admin/analytics");
    expect(mockApiFetch).toHaveBeenNthCalledWith(2, "/admin/analytics/chatbot?period=30d");

    const renderedText = tree!.root
      .findAll((node) => String(node.type) === "Text")
      .map((node) => node.props.children)
      .flat()
      .join(" ");

    expect(renderedText).toContain("Chatbot Demand");
    expect(renderedText).toContain("nike black t-shirt in xl");
    expect(renderedText).toContain("Nike Performance Black T-Shirt");
    expect(renderedText).toContain("33.3%");
  });
});