import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number, currency?: string) => string }) => unknown) => selector({ format: (value: number, currency = "AED") => `${currency} ${value.toFixed(2)}` }),
  formatCurrencyAmount: (value: number, currency = "AED") => `${currency} ${value.toFixed(2)}`,
}));

jest.mock("@/lib/icons", () =>
  new Proxy({}, { get: (_t: any, name: string) => () => <span data-testid={`icon-${String(name)}`} /> })
);

jest.mock("@/components/LogisticsPartnerLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

import LogisticsPartnerPayoutsPage from "@/app/logistics-partner/payouts/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Logistics payouts receipt workflow", () => {
  let receipts: any[];

  beforeEach(() => {
    jest.clearAllMocks();
    receipts = [];

    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/dashboard") {
        return okJson({
          payout_summary: {
            total_earned: 420,
            available_balance: 180,
            pending_amount: 80,
            completed_amount: 160,
            payout_count: 3,
          },
        });
      }
      if (path === "/logistics-partner/payouts") {
        return okJson([
          {
            id: 12,
            amount: 75,
            status: "processing",
            reference: "LP-PAYOUT-12",
            notes: "Awaiting payout",
            created_at: "2026-04-02T08:00:00Z",
            processed_at: null,
          },
        ]);
      }
      if (path === "/finance/logistics/summary") {
        return okJson({
          total_delivery_fees: 480,
          available_balance: 180,
          pending_payouts: 80,
          total_completed: 160,
          currency: "AED",
          has_pending_cod: true,
          pending_cod_amount: 100,
          bank_instruction: "Remit COD to Zozi treasury account and upload proof.",
        });
      }
      if (path === "/finance/logistics/settlements") {
        return okJson([
          {
            id: 77,
            order_id: 9001,
            total_delivery_fee: 18,
            currency: "AED",
            cod_collected: 120,
            cod_retained: 0,
            cod_remitted: 20,
            cod_remittance_status: "partial",
            status: "eligible",
            created_at: "2026-04-05T08:00:00Z",
          },
        ]);
      }
      if (path === "/logistics-partner/me/bank-account") {
        return okJson({});
      }
      if (path === "/logistics-partner/me/cod-remittance-receipts" && (!options || !options.method)) {
        return okJson(receipts);
      }
      if (path === "/logistics-partner/me/cod-remittance-receipts" && options?.method === "POST") {
        receipts = [
          {
            id: 501,
            settlement_id: 77,
            partner_id: 9,
            order_id: 9001,
            amount: 100,
            currency: "AED",
            bank_reference: "COD-DEP-501",
            receipt_file_url: "/uploads/logistics_cod_receipts/receipt-501.png",
            notes: "Bank branch deposit",
            status: "pending",
            review_note: null,
            created_at: "2026-04-06T08:00:00Z",
            due_amount: 120,
            remitted_before_receipt: 20,
            remaining_amount: 0,
          },
        ];
        return okJson(receipts[0]);
      }
      throw new Error(`Unhandled request ${path}`);
    });
  });

  it("submits COD proof from the logistics payout workspace", async () => {
    render(<LogisticsPartnerPayoutsPage />);

    await screen.findByText("COD Receipt Upload");

    fireEvent.change(screen.getByPlaceholderText("120.00"), { target: { value: "100" } });
    fireEvent.change(screen.getByPlaceholderText("Bank deposit reference"), { target: { value: "COD-DEP-501" } });
    fireEvent.change(screen.getByPlaceholderText("Optional note for finance review"), { target: { value: "Bank branch deposit" } });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeTruthy();
    fireEvent.change(fileInput, {
      target: { files: [new File(["proof"], "receipt.png", { type: "image/png" })] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Submit COD proof" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partner/me/cod-remittance-receipts",
        expect.objectContaining({ method: "POST", body: expect.any(FormData) }),
      );
    });

    expect(await screen.findByText("COD receipt submitted for finance verification.")).toBeInTheDocument();
    expect(await screen.findByText(/COD-DEP-501/)).toBeInTheDocument();
  });

  it("shows completed payout and remittance status after finance settlement", async () => {
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/dashboard") {
        return okJson({
          payout_summary: {
            total_earned: 520,
            available_balance: 40,
            pending_amount: 0,
            completed_amount: 480,
            payout_count: 4,
          },
        });
      }
      if (path === "/logistics-partner/payouts") {
        return okJson([
          {
            id: 44,
            amount: 180,
            status: "completed",
            reference: "LP-PAYOUT-44",
            notes: "Settled by finance transfer",
            created_at: "2026-04-07T08:00:00Z",
            processed_at: "2026-04-08T11:00:00Z",
          },
        ]);
      }
      if (path === "/finance/logistics/summary") {
        return okJson({
          total_delivery_fees: 520,
          available_balance: 40,
          pending_payouts: 0,
          total_completed: 480,
          currency: "AED",
          has_pending_cod: false,
          pending_cod_amount: 0,
          bank_instruction: "All COD reconciled.",
        });
      }
      if (path === "/finance/logistics/settlements") {
        return okJson([
          {
            id: 177,
            order_id: 9441,
            total_delivery_fee: 22,
            currency: "AED",
            cod_collected: 220,
            cod_retained: 22,
            cod_remitted: 198,
            cod_remittance_status: "complete",
            status: "settled",
            created_at: "2026-04-05T08:00:00Z",
          },
        ]);
      }
      if (path === "/logistics-partner/me/bank-account") {
        return okJson({});
      }
      if (path === "/logistics-partner/me/cod-remittance-receipts" && (!options || !options.method)) {
        return okJson([
          {
            id: 901,
            settlement_id: 177,
            partner_id: 9,
            order_id: 9441,
            amount: 198,
            currency: "AED",
            bank_reference: "COD-FULL-901",
            receipt_file_url: "/uploads/logistics_cod_receipts/receipt-901.png",
            notes: "Verified by finance",
            status: "verified",
            review_note: "Matched with bank statement",
            created_at: "2026-04-08T08:00:00Z",
            due_amount: 198,
            remitted_before_receipt: 0,
            remaining_amount: 0,
          },
        ]);
      }
      throw new Error(`Unhandled request ${path}`);
    });

    render(<LogisticsPartnerPayoutsPage />);

    await screen.findByText("Payout history");
    expect(await screen.findByText("LP-PAYOUT-44")).toBeInTheDocument();
    expect((await screen.findAllByText("Completed")).length).toBeGreaterThan(0);
    expect(await screen.findByText("complete")).toBeInTheDocument();
    expect((await screen.findAllByText("verified")).length).toBeGreaterThan(0);
  });
});


