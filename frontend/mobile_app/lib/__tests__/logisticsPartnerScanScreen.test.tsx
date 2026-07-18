import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockLookupLogisticsPartnerShipment = jest.fn();
const mockUpdateLogisticsPartnerShipmentStatus = jest.fn();
const mockCreateLogisticsPartnerShipmentConfirmationRequest = jest.fn();
const mockRouterPush = jest.fn();
let mockRouteCode = "ORDER-701";

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("View", props, children),
    Text: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("ScrollView", props, children),
    TextInput: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: { children?: React.ReactNode }) => React.createElement("TouchableOpacity", props, children),
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    StyleSheet: { create: (styles: unknown) => styles, absoluteFill: {} },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: mockRouterPush }),
  useLocalSearchParams: () => ({ code: mockRouteCode }),
}));

jest.mock("@/lib/api", () => ({
  lookupLogisticsPartnerShipment: (...args: unknown[]) => mockLookupLogisticsPartnerShipment(...args),
  updateLogisticsPartnerShipmentStatus: (...args: unknown[]) => mockUpdateLogisticsPartnerShipmentStatus(...args),
  createLogisticsPartnerShipmentConfirmationRequest: (...args: unknown[]) => mockCreateLogisticsPartnerShipmentConfirmationRequest(...args),
}));

jest.mock("@/components/SignaturePad", () => () => null);

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
        danger: "#cc0000",
        success: "#00aa00",
      },
      fontSize: {
        md: 16,
      },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    input: { borderWidth: 1, borderColor: "#dddddd" },
  }),
}));

import LogisticsPartnerScanScreen from "@/app/logistics-partner/scan";

describe("LogisticsPartnerScanScreen", () => {
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRouteCode = "ORDER-701";
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("auto-lookups the shipment from the incoming route code", async () => {
    mockLookupLogisticsPartnerShipment.mockResolvedValueOnce({
      id: 9901,
      order_id: 701,
      status: "picking_up",
      status_label: "picking up",
      carrier_name: "Falcon Express",
      tracking_number: null,
      scan_code: "SHIP-701-9901",
      current_hub: "Supplier Dispatch Hub",
      package_count: 2,
      package_weight_kg: 3.4,
      package_dimensions: "40x25x18 cm",
      packaging_notes: "Fragile luxury goods",
      customer_name: "Amina Customer",
      customer_phone: "+971 50 555 0101",
      shipping_address: "Palm Jumeirah, Dubai, UAE",
      delivery_location: "25.1124,55.1382",
      estimated_delivery: "2026-03-30T18:00:00Z",
      delivery_signature_name: null,
      delivery_signature_data_url: null,
      delivery_signature_captured_at: null,
    });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<LogisticsPartnerScanScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockLookupLogisticsPartnerShipment).toHaveBeenCalledWith("ORDER-701");

    const textInputs = tree!.root.findAll((node) => String(node.type) === "TextInput");
    expect(textInputs[0]?.props.value).toBe("ORDER-701");

    const renderedText = tree!.root
      .findAll((node) => String(node.type) === "Text")
      .map((node) => node.props.children)
      .flat()
      .join(" ");

    expect(renderedText).toContain("Shipment #9901");
    expect(renderedText).toContain("Order #701");
  });

  it("shows pending confirmation state when a shipment already has an approval request", async () => {
    mockLookupLogisticsPartnerShipment.mockResolvedValueOnce({
      id: 8801,
      order_id: 801,
      status: "shipped",
      status_label: "shipped",
      tracking_number: "TRK-8801",
      scan_code: "SHIP-8801",
      current_hub: "Dubai Hub",
      customer_name: "Amina Customer",
      active_confirmation_request: {
        id: 44,
        status: "pending",
        target_role: "customer",
        requested_status: "delivered",
        current_hub: "Dubai Hub",
        tracking_number: "TRK-8801",
        confirmation_type_label: "Delivery Confirmation",
      },
    });

    let tree: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<LogisticsPartnerScanScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const renderedText = tree!.root
      .findAll((node) => String(node.type) === "Text")
      .map((node) => node.props.children)
      .flat()
      .join(" ");

    expect(renderedText).toContain("request pending");
    expect(renderedText).toContain("Awaiting Confirmation");
    expect(renderedText).toContain("delivered");
  });

  it("requires a failure reason before marking a shipment failed", async () => {
    mockLookupLogisticsPartnerShipment.mockResolvedValueOnce({
      id: 7701,
      order_id: 771,
      status: "in_transit",
      status_label: "in transit",
      tracking_number: "TRK-7701",
      scan_code: "SHIP-7701",
      current_hub: "Muscat Hub",
      customer_name: "Salim Customer",
    });
    mockUpdateLogisticsPartnerShipmentStatus.mockResolvedValueOnce({
      status: "failed",
      status_label: "failed",
      current_hub: "Muscat Hub",
      tracking_number: "TRK-7701",
    });

    let tree!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      tree = TestRenderer.create(<LogisticsPartnerScanScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      tree.root.findByProps({ testID: "logistics-scan-action-failed-shipment_failed" }).props.onPress();
    });

    expect(tree.root.findByProps({ testID: "logistics-scan-failure-helper" })).toBeTruthy();

    await act(async () => {
      tree.root.findByProps({ testID: "logistics-scan-update" }).props.onPress();
    });

    const renderedText = tree.root
      .findAll((node) => String(node.type) === "Text")
      .map((node) => node.props.children)
      .flat()
      .join(" ");

    expect(renderedText).toContain("Add a failure or return reason before updating this shipment.");
    expect(mockUpdateLogisticsPartnerShipmentStatus).not.toHaveBeenCalled();

    await act(async () => {
      tree.root.findByProps({ testID: "logistics-scan-notes" }).props.onChangeText("Customer unreachable after repeated delivery attempts");
    });

    await act(async () => {
      await tree.root.findByProps({ testID: "logistics-scan-update" }).props.onPress();
    });

    expect(mockUpdateLogisticsPartnerShipmentStatus).toHaveBeenCalledWith(
      7701,
      expect.objectContaining({
        status: "failed",
        event_type: "shipment_failed",
        notes: "Customer unreachable after repeated delivery attempts",
      }),
    );
  });
});