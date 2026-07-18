import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockGetOrderTracking = jest.fn();
const mockRespondToShipmentConfirmation = jest.fn();
const mockOpenURL = jest.fn();
const mockSocketClose = jest.fn();
const mockRouter = { back: jest.fn(), replace: jest.fn() };

jest.mock("react-native", () => {
  const React = require("react");
  return {
    ActivityIndicator: (props: unknown) => React.createElement("ActivityIndicator", props),
    Image: (props: unknown) => React.createElement("Image", props),
    Linking: { openURL: (...args: unknown[]) => mockOpenURL(...args) },
    ScrollView: ({ children, ...props }: any) => React.createElement("ScrollView", props, children),
    StyleSheet: {
      create: (styles: unknown) => styles,
      absoluteFillObject: {},
    },
    Text: ({ children, ...props }: any) => React.createElement("Text", props, children),
    TextInput: ({ children, ...props }: any) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: any) => React.createElement("TouchableOpacity", props, children),
    View: ({ children, ...props }: any) => React.createElement("View", props, children),
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
  useLocalSearchParams: () => ({ id: "42" }),
  useRouter: () => mockRouter,
}));

jest.mock("@/lib/api", () => ({
  API_BASE: "http://localhost:8000",
  getCurrentAccessToken: jest.fn(() => "mobile-live-token"),
  getOrderTracking: (...args: unknown[]) => mockGetOrderTracking(...args),
  respondToShipmentConfirmation: (...args: unknown[]) => mockRespondToShipmentConfirmation(...args),
}));

jest.mock("@/lib/authStore", () => ({
  useAuthStore: () => ({
    user: { id: 9, role: "customer" },
    isLoggedIn: true,
    isLoading: false,
  }),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        surface1: "#ffffff",
        surface2: "#f7f7f7",
        border: "#dddddd",
        text: "#111111",
        textMuted: "#666666",
        success: "#009944",
        danger: "#cc0000",
      },
      fontSize: { xs: 12, sm: 14, md: 16 },
      spacing: { sm: 8, md: 12 },
      radius: { xl: 16, lg: 12 },
    },
  }),
}));

jest.mock("@/components/ui/Badge", () => ({
  Badge: ({ label }: any) => React.createElement("Text", null, label),
}));

jest.mock("@/components/ui/LoadingSpinner", () => ({
  LoadingSpinner: () => null,
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    container: { flex: 1 },
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    textBrand: { color: "#123456" },
    input: { borderWidth: 1 },
  }),
}));

jest.mock("@shared/realtime", () => ({
  openRealtimeSocket: () => ({ close: mockSocketClose }),
}));

jest.mock("@shared/trackingMap", () => ({
  buildTrackingMapHref: (latitude: number, longitude: number) => `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}`,
  extractTrackingMapPoints: () => ([
    {
      shipmentId: 91,
      label: "Shipment #91 · Falcon Supplier",
      latitude: 25.2048,
      longitude: 55.2708,
      location: "Dubai Sortation Hub",
      currentHub: "Dubai Hub",
      recordedAt: "2026-05-09T10:30:00Z",
    },
  ]),
}));

import TrackingScreen from "@/app/tracking/[id]";

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

describe("TrackingScreen render", () => {
  jest.setTimeout(15000);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders shipment proof, confirmation, event trail, and carrier tracking launch", async () => {
    const trackingPayload = {
      order_id: 42,
      order_status: "in_transit",
      order_status_label: "In Transit",
      delivered_shipments: 0,
      shipment_count: 1,
      tracking_numbers: ["TRK-42"],
      available_scan_codes: ["SCAN-42"],
      timeline: [
        { key: "placed", label: "Placed", completed: true, active: false },
        { key: "in_transit", label: "In Transit", completed: false, active: true, notes: "Courier is moving" },
      ],
      items: [
        { product_id: 7, product_name: "Falcon Speaker", quantity: 1, price: 199, supplier_id: 5 },
      ],
      shipments: [
        {
          id: 91,
          order_id: 42,
          supplier_id: 5,
          supplier_name: "Falcon Supplier",
          status: "in_transit",
          status_label: "In Transit",
          current_hub: "Dubai Hub",
          distribution_channel: "express",
          tracking_number: "TRK-42",
          tracking_url: "https://carrier.example/TRK-42",
          scan_code: "SCAN-42",
          package_count: 1,
          package_weight_kg: 2.4,
          package_dimensions: "20x10x8 cm",
          packaged_at: "2026-05-09T09:00:00Z",
          packaging_notes: "Fragile audio equipment",
          shipping_address: "Business Bay, Dubai",
          estimated_delivery: "2026-05-10T09:00:00Z",
          delivery_signature_name: "Amina Khan",
          delivery_signature_data_url: "data:image/png;base64,abc123",
          delivery_signature_captured_at: "2026-05-09T11:00:00Z",
          active_confirmation_request: {
            id: 301,
            confirmation_type: "delivery_confirmation",
            confirmation_type_label: "Delivery Confirmation",
            requested_status: "delivered",
            target_role: "customer",
            target_user_id: 9,
            tracking_number: "TRK-42",
            current_hub: "Dubai Hub",
            notes: "Confirm handoff at reception",
          },
          events: [
            {
              id: 1,
              shipment_id: 91,
              order_id: 42,
              supplier_id: 5,
              actor_role: "logistics_partner",
              event_type: "distribution_checkpoint",
              event_label: "Distribution Checkpoint",
              location: "Dubai Sortation Hub",
              notes: "Manifest verified",
              created_at: "2026-05-09T10:30:00Z",
              latitude: 25.2048,
              longitude: 55.2708,
            },
          ],
        },
      ],
      shipping_address: "Business Bay, Dubai",
      delivery_location: "Tower A",
      customer_phone: "+971500000000",
      delivery_note: "Call on arrival",
      subtotal_amount: 199,
      shipping_amount: 15,
      vat_amount: 10,
      total_amount: 224,
    };
    mockGetOrderTracking.mockResolvedValue(trackingPayload);
    mockRespondToShipmentConfirmation.mockResolvedValue({ ok: true });

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<TrackingScreen />);
    });
    await act(async () => {});

    const text = getRenderedText(renderer);
    expect(text).toContain("Shipment Journey");
    expect(text).toContain("Pending Confirmation");
    expect(text).toContain("Open carrier tracking");
    expect(text).toContain("Delivery Signature");
    expect(text).toContain("Event Trail");
    expect(text).toContain("Latest GPS checkpoints");

    expect(renderer.root.findByProps({ testID: "tracking-signature-91" })).toBeTruthy();

    await act(async () => {
      renderer.root.findByProps({ testID: "tracking-carrier-link-91" }).props.onPress();
    });

    expect(mockOpenURL).toHaveBeenCalledWith("https://carrier.example/TRK-42");

    await act(async () => {
      renderer.root.findByProps({ testID: "tracking-map-point-91" }).props.onPress();
    });

    expect(mockOpenURL).toHaveBeenCalledWith("https://www.openstreetmap.org/?mlat=25.2048&mlon=55.2708");

    await act(async () => {
      renderer.root.findByProps({ testID: "tracking-signature-open-91" }).props.onPress();
    });

    expect(mockOpenURL).toHaveBeenCalledWith("data:image/png;base64,abc123");

    await act(async () => {
      renderer.root.findByProps({ testID: "tracking-confirmation-note-301" }).props.onChangeText("Delivered to reception desk");
    });

    await act(async () => {
      await renderer.root.findByProps({ testID: "tracking-confirmation-accept-301" }).props.onPress();
    });

    expect(mockRespondToShipmentConfirmation).toHaveBeenCalledWith(42, 301, {
      decision: "accepted",
      response_notes: "Delivered to reception desk",
    });
    expect(mockGetOrderTracking).toHaveBeenCalledTimes(2);
    expect(getRenderedText(renderer)).toContain("Confirmation accepted.");

    await act(async () => {
      renderer.unmount();
    });

    expect(mockSocketClose).toHaveBeenCalled();
  });
});
