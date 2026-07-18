import React from "react";
import TestRenderer, { act } from "react-test-renderer";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const mockGetSupplierFinanceSummary = jest.fn();
const mockGetSupplierFinanceSettlements = jest.fn();
const mockGetSupplierPayouts = jest.fn();
const mockGetSupplierBankAccount = jest.fn();
const mockUpsertSupplierBankAccount = jest.fn();

jest.mock("react-native", () => {
  const React = require("react");
  return {
    View: ({ children, ...props }: any) => React.createElement("View", props, children),
    Text: ({ children, ...props }: any) => React.createElement("Text", props, children),
    ScrollView: ({ children, ...props }: any) => React.createElement("ScrollView", props, children),
    StyleSheet: { create: (styles: unknown) => styles },
    ActivityIndicator: (props: any) => React.createElement("ActivityIndicator", props),
    RefreshControl: (props: any) => React.createElement("RefreshControl", props),
    TextInput: ({ children, ...props }: any) => React.createElement("TextInput", props, children),
    TouchableOpacity: ({ children, ...props }: any) => React.createElement("TouchableOpacity", props, children),
    Alert: { alert: jest.fn() },
  };
});

jest.mock("expo-router", () => ({
  Stack: { Screen: () => null },
}));

jest.mock("@/lib/api", () => ({
  getSupplierFinanceSummary: (...args: unknown[]) => mockGetSupplierFinanceSummary(...args),
  getSupplierFinanceSettlements: (...args: unknown[]) => mockGetSupplierFinanceSettlements(...args),
  getSupplierPayouts: (...args: unknown[]) => mockGetSupplierPayouts(...args),
  getSupplierBankAccount: (...args: unknown[]) => mockGetSupplierBankAccount(...args),
  upsertSupplierBankAccount: (...args: unknown[]) => mockUpsertSupplierBankAccount(...args),
}));

jest.mock("@/lib/themeStore", () => ({
  useThemeStore: () => ({
    theme: {
      colors: {
        brand: "#123456",
        surface0: "#f8fafc",
        surface1: "#ffffff",
        border: "#dddddd",
        text: "#111111",
        textMuted: "#666666",
        textFaint: "#999999",
      },
      spacing: { xs: 4, md: 16 },
      radius: { lg: 16, xl: 20 },
      fontSize: { xs: 12, sm: 14, md: 16, lg: 20, "3xl": 30 },
    },
  }),
}));

jest.mock("@/theme", () => ({
  makeStyles: () => ({
    text: { color: "#111111" },
    textMuted: { color: "#666666" },
    title: { color: "#111111" },
  }),
}));

jest.mock("@/components/ui/EmptyState", () => ({
  EmptyState: ({ title, subtitle }: any) => React.createElement("View", null, React.createElement("Text", null, title), React.createElement("Text", null, subtitle)),
}));

import SupplierPayoutsScreen from "@/app/supplier/payouts";

function flattenText(value: unknown): string {
  if (Array.isArray(value)) return value.map(flattenText).join(" ");
  if (value == null || typeof value === "boolean") return "";
  return String(value);
}

function getRenderedText(renderer: TestRenderer.ReactTestRenderer): string {
  return renderer.root
    .findAll((node) => String(node.type) === "Text")
    .map((node) => flattenText(node.props.children))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

describe("SupplierPayoutsScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders settlement route, allocation, commission rate, and refund detail", async () => {
    mockGetSupplierFinanceSummary.mockResolvedValueOnce({
      total_gross_revenue: 1000,
      total_net_earnings: 800,
      pending_settlement: 120,
      total_settled: 680,
      total_vat_on_orders: 50,
      total_refund_reversals: 20,
      total_orders: 12,
    });
    mockGetSupplierFinanceSettlements.mockResolvedValueOnce([
      {
        id: 1,
        supplier_id: 9,
        order_id: 501,
        gross_amount: 100,
        commission_rate: 12.5,
        commission_deducted: 12.5,
        vat_on_commission: 0.63,
        net_amount: 82.87,
        status: "eligible",
        currency: "AED",
        created_at: "2026-05-10T09:00:00Z",
        payment_method: "tap",
        vat_amount: 5,
        delivery_total: 20,
        destination_city: "Muscat",
        destination_country: "Oman",
        partner_name: "Falcon Express",
        service_area_label: "North Route",
        allocation_source: "partner_route",
        refund_status: "partial",
        supplier_reversal_amount: 5,
        customer_refund_amount: 15,
      },
    ]);
    mockGetSupplierPayouts.mockResolvedValueOnce([
      {
        id: 10,
        amount: 200,
        status: "pending",
        created_at: "2026-05-10T09:00:00Z",
      },
    ]);
    mockGetSupplierBankAccount.mockResolvedValueOnce(null);

    let renderer!: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<SupplierPayoutsScreen />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const text = getRenderedText(renderer);
    expect(text).toContain("Supplier Finance Summary");
    expect(text).toContain("Destination Muscat, Oman");
    expect(text).toContain("Allocation partner route");
    expect(text).toContain("Commission Rate 12.5%");
    expect(text).toContain("Delivery Total AED 20.00");
    expect(text).toContain("Customer refund AED 15.00");
  });
});