import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
let currentAuthState: Record<string, unknown>;

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  parseJsonResponse: async (response: { json: () => Promise<unknown> }) => response.json(),
  getErrorMessage: (payload: any) => payload?.detail || payload?.message || "Request failed",
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => unknown) => selector({ format: (value: number) => `AED ${value.toFixed(2)}` }),
  formatCurrencyAmount: (value: number, currency = "AED") => `${currency} ${value.toFixed(2)}`,
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "compact", setDensity: jest.fn() }),
  dc: (_d: any, compact: any, _normal: any, _expanded: any) => compact,
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => currentAuthState,
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: ({ rows, columns, rowActions }: any) => (
    <table>
      <tbody>
        {(rows ?? []).map((row: any, i: number) => (
          <tr key={i}>
            {(columns ?? []).map((col: any) => (
              <td key={col.key}>{col.render ? col.render(row) : String(row[col.key] ?? "")}</td>
            ))}
            {rowActions && <td>{rowActions(row)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}));

jest.mock("@/lib/backgroundJobs", () => ({
  trackBackgroundJob: jest.fn(),
}));

import FinanceTab from "@/app/admin/dashboard/_tabs/FinanceTab";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin finance COD verification", () => {
  let receiptRows: any[];
  let ledgerRows: any[];
  let supplierSettlements: any[];
  let logisticsSettlements: any[];

  beforeEach(() => {
    jest.clearAllMocks();
    currentAuthState = { user: { id: 1, role: "admin", username: "admin" }, isLoggedIn: true, isLoading: false };
    receiptRows = [
      {
        id: 41,
        settlement_id: 12,
        partner_id: 7,
        partner_name: "RapidFleet",
        partner_code: "RAPID-7",
        order_id: 3201,
        amount: 120,
        currency: "AED",
        bank_reference: "COD-VERIFY-41",
        receipt_file_url: "/uploads/logistics_cod_receipts/verify-41.png",
        status: "pending",
        review_note: null,
        created_at: "2026-04-06T08:00:00Z",
        reviewed_at: null,
        due_amount: 120,
        remitted_before_receipt: 0,
        remaining_amount: 0,
      },
    ];

    ledgerRows = [];
    supplierSettlements = [];
    logisticsSettlements = [];

    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/finance/admin/summary") return okJson({ total_revenue: 1000, total_supplier_payable: 600, total_logistics_payable: 120, pending_cod_remittances: 120, unreconciled_bank_txns: 1, net_zozi_revenue: 280 });
      if (path === "/finance/dashboard/metrics") return okJson({ total_revenue: 1000, total_expenses: 400, net_profit: 600 });
      if (path === "/finance/cash-position") return okJson({ balance: 50000, currency: "AED" });
      if (path === "/admin/orders?limit=500") return okJson([]);
      if (path === "/finance/admin/ledger?limit=200") return okJson(ledgerRows);
      if (path === "/finance/admin/supplier-settlements?limit=200") return okJson(supplierSettlements);
      if (path === "/finance/admin/logistics-settlements?limit=200") return okJson(logisticsSettlements);
      if (path === "/finance/admin/refunds?limit=200") return okJson([]);
      if (path === "/finance/admin/transfer-providers") return okJson({ default_provider: "manual", providers: [{ key: "manual", name: "Manual", configured: true, missing_requirements: [] }] });
      if (path === "/admin/suppliers/all?page_size=200") return okJson({ items: [] });
      if (path === "/finance/admin/cod-remittance-receipts?limit=50" && (!options || !options.method)) return okJson(receiptRows);
      if (path === "/finance/admin/payouts/supplier/process" && options?.method === "POST") {
        return okJson({ processed: 1, payouts: [{ payout_id: 701, supplier_id: 88, amount: 320, order_count: 1, reference: "SUP-701" }] });
      }
      if (path === "/finance/admin/payouts/logistics/process" && options?.method === "POST") {
        return okJson({ processed: 1, payouts: [{ payout_id: 801, partner_id: 52, amount: 45, delivery_count: 1, reference: "LOG-801" }] });
      }
      if (path.startsWith("/finance/admin/payouts/supplier/dispatch") && options?.method === "POST") {
        return okJson({ id: "job-supplier-1", status: "queued" });
      }
      if (path.startsWith("/finance/admin/payouts/logistics/dispatch") && options?.method === "POST") {
        return okJson({ id: "job-logistics-1", status: "queued" });
      }
      if (path === "/finance/admin/cod-remittance-receipts/41/verify" && options?.method === "POST") {
        receiptRows = [{ ...receiptRows[0], status: "verified", review_note: "Verified in finance workspace" }];
        return okJson(receiptRows[0]);
      }
      throw new Error(`Unhandled request ${path}`);
    });
  });

  it("verifies a pending COD receipt from finance", async () => {
    render(<FinanceTab />);

    await screen.findByText("COD Receipt Verification");
    await screen.findByText("RapidFleet");

    fireEvent.click(screen.getByRole("button", { name: /Verify/i }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/finance/admin/cod-remittance-receipts/41/verify",
        expect.objectContaining({ method: "POST" }),
      );
    });

    expect(await screen.findByText("COD receipt #41 verified and reconciled.")).toBeInTheDocument();
    expect(await screen.findByText("Verified in finance workspace")).toBeInTheDocument();
  });

  it("shows payout selection checkboxes and processes selected settlements", async () => {
    ledgerRows = [
      {
        id: 9901,
        order_id: 510,
        supplier_id: 88,
        logistics_partner_id: 52,
        payment_method: "card",
        product_subtotal: 300,
        discount_amount: 0,
        delivery_total: 45,
        vat_amount: 20,
        net_supplier_amount: 320,
        net_logistics_amount: 45,
        cod_remittance_due: 0,
        settlement_status: "pending",
        created_at: "2026-04-06T08:00:00Z",
        supplier: { id: 88, username: "supplier_88", profile: { business_name: "S88 Trading" } },
      },
    ];
    supplierSettlements = [
      { id: 7001, order_id: 510, supplier_id: 88, net_amount: 320, status: "eligible", eligible_at: "2026-04-06T08:00:00Z" },
    ];
    logisticsSettlements = [
      {
        id: 8001,
        order_id: 510,
        partner_id: 52,
        total_delivery_fee: 45,
        cod_collected: 0,
        cod_remitted: 0,
        cod_remittance_status: "n/a",
        status: "eligible",
        eligible_at: "2026-04-06T08:00:00Z",
      },
    ];

    render(<FinanceTab />);

    await screen.findByText("Order Settlement Table");

    const selectSupplier = await screen.findByRole("checkbox", { name: /Supplier payout selection/i });
    const selectLogistics = await screen.findByRole("checkbox", { name: /Logistics payout selection/i });
    fireEvent.click(selectSupplier);
    fireEvent.click(selectLogistics);
    fireEvent.click(screen.getByRole("button", { name: /Proceed Selected Payouts/i }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/finance/admin/payouts/supplier/process",
        expect.objectContaining({ method: "POST", body: JSON.stringify({ settlement_ids: [7001] }) }),
      );
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/finance/admin/payouts/logistics/process",
        expect.objectContaining({ method: "POST", body: JSON.stringify({ settlement_ids: [8001] }) }),
      );
    });
  });

  it("treats complete COD remittance status as received", async () => {
    ledgerRows = [
      {
        id: 1201,
        order_id: 3201,
        supplier_id: 23,
        logistics_partner_id: 7,
        payment_method: "cod",
        product_subtotal: 100,
        discount_amount: 0,
        delivery_total: 10,
        vat_amount: 5,
        net_supplier_amount: 90,
        net_logistics_amount: 10,
        cod_remittance_due: 0,
        settlement_status: "pending",
        created_at: "2026-04-06T08:00:00Z",
        supplier: { id: 23, username: "supplier_23", profile: { business_name: "S23 Logistics" } },
      },
    ];
    supplierSettlements = [
      { id: 7101, order_id: 3201, supplier_id: 23, net_amount: 90, status: "settled", eligible_at: "2026-04-06T08:00:00Z" },
    ];
    logisticsSettlements = [
      {
        id: 8101,
        order_id: 3201,
        partner_id: 7,
        total_delivery_fee: 10,
        cod_collected: 0,
        cod_remitted: 0,
        cod_remittance_status: "complete",
        status: "settled",
        eligible_at: "2026-04-06T08:00:00Z",
      },
    ];

    render(<FinanceTab />);

    expect(await screen.findByText("Received")).toBeInTheDocument();
  });

  it("marks completed supplier and logistics settlements as closed transactions", async () => {
    ledgerRows = [
      {
        id: 1301,
        order_id: 4101,
        supplier_id: 31,
        logistics_partner_id: 9,
        payment_method: "card",
        product_subtotal: 220,
        discount_amount: 0,
        delivery_total: 25,
        vat_amount: 12,
        net_supplier_amount: 198,
        net_logistics_amount: 25,
        cod_remittance_due: 0,
        settlement_status: "pending",
        created_at: "2026-04-06T08:00:00Z",
        supplier: { id: 31, username: "supplier_31", profile: { business_name: "S31 Premium" } },
      },
    ];
    supplierSettlements = [
      { id: 7201, order_id: 4101, supplier_id: 31, net_amount: 198, status: "completed", eligible_at: "2026-04-06T08:00:00Z" },
    ];
    logisticsSettlements = [
      {
        id: 8201,
        order_id: 4101,
        partner_id: 9,
        total_delivery_fee: 25,
        cod_collected: 0,
        cod_remitted: 0,
        cod_remittance_status: "n/a",
        status: "completed",
        eligible_at: "2026-04-06T08:00:00Z",
      },
    ];

    render(<FinanceTab />);

    expect(await screen.findByText("Closed")).toBeInTheDocument();
  });
});


