import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockApiFetch = jest.fn();
const mockGetLogisticsPartnerDashboard = jest.fn();
const mockRouterPush = jest.fn();
const mockRouterReplace = jest.fn();

let currentUser: { id: number; username: string; role: string } | null = null;

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    StyleSheet: {
      create: (styles: unknown) => styles,
      absoluteFill: {},
      absoluteFillObject: {},
    },
    Linking: { openURL: jest.fn() },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush, replace: mockRouterReplace }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  getLogisticsPartnerDashboard: (...args: unknown[]) => mockGetLogisticsPartnerDashboard(...args),
  getCurrentAccessToken: () => null,
  API_BASE: "https://api.example.test",
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({
    user: currentUser,
    logout: jest.fn(),
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        border: "#d4d4d8",
        text: "#111111",
        textMuted: "#666666",
        info: "#0ea5e9",
        success: "#16a34a",
        warning: "#f59e0b",
      },
      spacing: { xs: 8, sm: 12, md: 16 },
      radius: { lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, lg: 20, xl: 24, base: 16 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    row: { flexDirection: "row" },
    title: { color: "#111111" },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
  }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => unknown) =>
    selector({ format: (value: number) => `AED ${Number(value || 0).toFixed(2)}` }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: { locale: string }) => unknown) => selector({ locale: "en" }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text: string) => text,
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@/components/ui/Button", () => {
  const React = require("react");
  return {
    Button: ({ label, onPress, ...props }: { label: string; onPress?: () => void }) =>
      React.createElement(
        "TouchableOpacity",
        { onPress, ...props },
        React.createElement("Text", null, label),
      ),
  };
});

jest.mock("@shared/localization", () => ({
  isRtlLocale: () => false,
  formatLocalizedDate: () => "Mar 30",
  formatLocalizedDateTime: () => "Mar 30, 18:00",
}));

const SupplierDashboard = require("../../app/supplier/dashboard").default;
const LogisticsPartnerDashboard = require("../../app/logistics-partner/dashboard").default;

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

async function flush() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("mobile partner dashboard screens", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    currentUser = { id: 1, username: "Amina Partner", role: "supplier" };
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renders the supplier dashboard with onboarding, alerts, and product navigation", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/supplier/analytics/summary") {
        return Promise.resolve({
          total_revenue: 4120,
          total_orders: 23,
          total_products: 11,
          pending_orders: 4,
        });
      }
      if (url === "/supplier/inventory/alerts") {
        return Promise.resolve({
          alerts: [
            {
              type: "low_stock",
              product_id: 91,
              product_name: "Silk Abaya",
              current_stock: 3,
              message: "Stock is running low",
            },
          ],
        });
      }
      if (url === "/supplier/onboarding/status") {
        return Promise.resolve({
          profile_complete: false,
          terms_accepted: false,
          first_product_uploaded: false,
          products_count: 0,
          verification_status: "pending",
        });
      }
      if (url === "/supplier/badge") {
        return Promise.resolve({
          credibility_score: 72,
          badge_level: "silver",
          eligible_badge_level: "gold",
        });
      }
      return Promise.resolve(null);
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierDashboard />);
    });
    await flush();

    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/analytics/summary");
    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/inventory/alerts");
    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/onboarding/status");
    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/badge");

    const text = getRenderedText(renderer);
    expect(text).toContain("Welcome back");
    expect(text).toContain("Stock Alerts");
    expect(text).toContain("Silk Abaya");
    expect(text).toContain("Getting Started");
    expect(text).toContain("AED 4120.00");
    expect(text).toContain("Product Management");
    expect(text).toContain("Credibility Snapshot");
    expect(text).toContain("Trust Score");
    expect(text).toContain("72 /100");
    expect(text).toContain("Silver");
    expect(text).toContain("Gold");

    const quickAction = findTouchableByLabel(renderer, "Open Product Management");
    act(() => {
      quickAction.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/supplier/products");

    const credibilityButton = findTouchableByLabel(renderer, "Open Credibility");
    act(() => {
      credibilityButton.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/supplier/credibility");
  });

  it("renders the logistics dashboard metrics and opens the shipments route", async () => {
    currentUser = { id: 2, username: "Falcon Fleet", role: "logistics_partner" };
    mockGetLogisticsPartnerDashboard.mockResolvedValueOnce({
      stats: { total: 18, active: 6, delivered: 9, pending: 2, failed: 1 },
      analytics: {
        delivery_rate: 94.4,
        average_transit_hours: 5.5,
        scan_compliance_rate: 97.2,
        sla_on_time_rate: 92.1,
      },
      channel_breakdown: { marketplace: 10, b2b: 8 },
      payout_summary: {
        total_earned: 8500,
        available_balance: 2100,
        pending_amount: 700,
        completed_amount: 5700,
      },
      route_plan: {
        total_stops: 4,
        estimated_distance_km: 38.5,
        estimated_duration_hours: 3.2,
        stops: [
          {
            shipment_id: 701,
            stop_number: 1,
            distance_from_previous_km: 0,
            current_hub: "Dubai South",
            location: "Dubai South",
            tracking_number: "TRACK-701",
          },
        ],
      },
      sla_alerts: [
        {
          shipment_id: 701,
          overdue_hours: 1.5,
          current_hub: "Dubai South",
          estimated_delivery: "2026-03-30T18:00:00Z",
        },
      ],
      active_shipments: [
        {
          id: 701,
          status: "in_transit",
          tracking_number: "TRACK-701",
          carrier_name: "Falcon Express",
          current_hub: "Dubai South",
          estimated_delivery: "2026-03-30T18:00:00Z",
        },
      ],
      live_locations: [
        {
          shipment_id: 701,
          latitude: 25.2048,
          longitude: 55.2708,
          current_hub: "Dubai South",
          location: "Dubai South",
          tracking_number: "TRACK-701",
        },
      ],
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<LogisticsPartnerDashboard />);
    });
    await flush();

    expect(mockGetLogisticsPartnerDashboard).toHaveBeenCalledTimes(1);

    const text = getRenderedText(renderer);
    expect(text).toContain("Partner Dashboard");
    expect(text).toContain("Operational Analytics");
    expect(text).toContain("Distribution Channels");
    expect(text).toContain("Live Fleet Map");
    expect(text).toContain("Shipment");
    expect(text).toContain("701");
    expect(text).toContain("AED 8500.00");

    const shipmentsButton = findTouchableByLabel(renderer, "View Shipments");
    act(() => {
      shipmentsButton.props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/logistics-partner/shipments");
  });
});
