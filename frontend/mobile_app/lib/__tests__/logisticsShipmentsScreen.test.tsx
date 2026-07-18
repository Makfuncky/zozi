import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { Linking } from "react-native";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockGetLogisticsPartnerShipments = jest.fn();
const mockUpdateLogisticsPartnerShipmentStatus = jest.fn();
const mockRouterPush = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    Platform: { OS: "android", select: (options: Record<string, unknown>) => options.android ?? options.default ?? null },
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    FlatList: ({ data = [], renderItem, ListHeaderComponent, ListEmptyComponent, ListFooterComponent, ...props }: any) =>
      React.createElement(
        "FlatList",
        props,
        ListHeaderComponent ?? null,
        data.length
          ? data.map((item: unknown, index: number) => React.createElement(React.Fragment, { key: index }, renderItem({ item, index })))
          : ListEmptyComponent ?? null,
        ListFooterComponent ?? null,
      ),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Modal: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Modal", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    RefreshControl: (props: unknown) => React.createElement("RefreshControl", props),
    Alert: { alert: jest.fn() },
    Linking: { openURL: jest.fn() },
    StyleSheet: { create: (styles: unknown) => styles },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush }),
}));

jest.mock("@/lib/api", () => ({
  getLogisticsPartnerShipments: (...args: unknown[]) => mockGetLogisticsPartnerShipments(...args),
  updateLogisticsPartnerShipmentStatus: (...args: unknown[]) => mockUpdateLogisticsPartnerShipmentStatus(...args),
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
        success: "#16a34a",
        warning: "#f59e0b",
        danger: "#dc2626",
        surface1: "#ffffff",
        surface2: "#f1f5f9",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
      },
      spacing: { md: 16 },
      radius: { md: 12, lg: 16, xl: 20 },
      fontSize: { xs: 12, md: 16, lg: 20 },
    },
  }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    title: { color: "#111111" },
  }),
}));

jest.mock("@/components/ui/LoadingSkeleton", () => ({
  Skeleton: () => null,
}));

jest.mock("@shared/localization", () => ({
  formatLocalizedDate: (value: string) => value,
  formatLocalizedDateTime: (value: string) => value,
  isRtlLocale: () => false,
}));

const LogisticsPartnerShipments = require("../../app/logistics-partner/shipments").default;

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

function makeShipment(overrides: Record<string, unknown>) {
  return {
    id: 101,
    status: "prepared",
    order_id: 55,
    estimated_partner_payout: 22,
    order_payment_status: "paid",
    settlement_status: "pending",
    active_confirmation_request: null,
    delivery_signature_captured_at: null,
    ...overrides,
  };
}

describe("logistics shipments screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("accepts a prepared pickup directly from the shipments queue", async () => {
    mockGetLogisticsPartnerShipments.mockResolvedValue({
      items: [makeShipment({ id: 101, status: "prepared" })],
      total: 1,
      page: 1,
      total_pages: 1,
    });
    mockUpdateLogisticsPartnerShipmentStatus.mockResolvedValue({ status: "picking_up" });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<LogisticsPartnerShipments />);
    });

    expect(renderer.root.findByProps({ testID: "logistics-shipments-screen" })).toBeTruthy();
    expect(getRenderedText(renderer)).toContain("Receipt & Reconciliation");
    expect(getRenderedText(renderer)).toContain("Settlement open");

    await act(async () => {
      await renderer.root.findByProps({ testID: "logistics-shipments-accept-101" }).props.onPress();
    });

    expect(mockUpdateLogisticsPartnerShipmentStatus).toHaveBeenCalledWith(
      101,
      expect.objectContaining({
        status: "picking_up",
        event_type: "pickup_confirmed",
      }),
    );
  });

  it("opens the manage-pickup modal and saves a pickup cancellation update", async () => {
    mockGetLogisticsPartnerShipments.mockResolvedValue({
      items: [makeShipment({ id: 202, status: "picking_up", active_confirmation_request: { status: "pending" }, delivery_signature_captured_at: "2026-05-09T10:00:00Z" })],
      total: 1,
      page: 1,
      total_pages: 1,
    });
    mockUpdateLogisticsPartnerShipmentStatus.mockResolvedValue({ status: "prepared" });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<LogisticsPartnerShipments />);
    });

    const text = getRenderedText(renderer);
    expect(text).toContain("Pending confirmation");
    expect(text).toContain("Proof captured");

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-manage-202" }).props.onPress();
    });

    expect(renderer.root.findByProps({ testID: "logistics-shipments-update-modal" })).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-event-note" }).props.onChangeText("Pickup cancelled by dispatcher");
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "logistics-shipments-save-update" }).props.onPress();
    });

    expect(mockUpdateLogisticsPartnerShipmentStatus).toHaveBeenCalledWith(
      202,
      expect.objectContaining({
        status: "prepared",
        release_assignment: true,
        event_type: "pickup_cancelled",
        notes: "Pickup cancelled by dispatcher",
      }),
    );
  });

  it("opens pickup and dropoff maps and routes into scan and tracker flows", async () => {
    mockGetLogisticsPartnerShipments.mockResolvedValue({
      items: [makeShipment({
        id: 303,
        status: "in_transit",
        order_id: 909,
        tracking_number: "TRK-303",
        scan_code: "SCAN-303",
        supplier_pickup_address: "Warehouse 4, Dubai",
        supplier_pickup_location: "25.2048,55.2708",
        customer_dropoff_address: "Palm Jumeirah, Dubai",
        customer_dropoff_location: "25.1124,55.1390",
      })],
      total: 1,
      page: 1,
      total_pages: 1,
    });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<LogisticsPartnerShipments />);
    });

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-open-pickup-map-303" }).props.onPress();
    });

    expect(Linking.openURL).toHaveBeenCalledWith(
      "https://www.google.com/maps/search/?api=1&query=Warehouse%204%2C%20Dubai%2025.2048%2C55.2708",
    );

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-open-dropoff-map-303" }).props.onPress();
    });

    expect(Linking.openURL).toHaveBeenCalledWith(
      "https://www.google.com/maps/search/?api=1&query=Palm%20Jumeirah%2C%20Dubai%2025.1124%2C55.1390",
    );

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-open-scan-303" }).props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/logistics-partner/scan?code=SCAN-303");

    await act(async () => {
      renderer.root.findByProps({ testID: "logistics-shipments-open-tracker-303" }).props.onPress();
    });

    expect(mockRouterPush).toHaveBeenCalledWith("/tracking/909");
  });
});