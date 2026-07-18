import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockAddToast = jest.fn();
const mockReplace = jest.fn();
const mockPush = jest.fn();
const mockUseSearchParams = jest.fn(() => new URLSearchParams());

let payoutRows: Array<Record<string, unknown>> = [];
let invoiceRows: Array<Record<string, unknown>> = [];

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: mockPush, prefetch: jest.fn() }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: (state: { addToast: typeof mockAddToast }) => unknown) => selector({ addToast: mockAddToast }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => unknown) => selector({ format: (value: number) => `AED ${value.toFixed(2)}` }),
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "comfortable" }),
  dc: (_density: string, _compact: string, regular: string, _roomy: string) => regular,
}));

jest.mock("@/components/SupplierLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  ),
}));

jest.mock("@/app/supplier/payouts/FinanceSection", () => ({
  __esModule: true,
  default: () => <div data-testid="supplier-finance-section">Supplier finance section</div>,
}));

import SupplierPayoutsPage from "@/app/supplier/payouts/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

function wireApiFetch() {
  mockApiFetch.mockImplementation((path: string, options?: { body?: string }) => {
    if (path === "/supplier/payouts") {
      return Promise.resolve(okJson(payoutRows));
    }

    if (path === "/invoices/?page=1&page_size=10") {
      return Promise.resolve(okJson({ items: invoiceRows, total: invoiceRows.length, total_pages: 1 }));
    }

    if (path === "/supplier/payouts/request") {
      const body = JSON.parse(String(options?.body || "{}"));
      const created = {
        id: 303,
        amount: body.amount,
        status: "pending",
        method: "bank",
        reference: null,
        notes: body.notes,
        created_at: "2026-04-09T10:00:00Z",
        processed_at: null,
      };
      payoutRows = [created, ...payoutRows];
      return Promise.resolve(okJson(created));
    }

    if (path === "/invoices/") {
      const body = JSON.parse(String(options?.body || "{}"));
      const created = {
        id: 51,
        invoice_number: "INV-NEW",
        order_id: body.order_id,
        total_amount: 87.5,
        currency: body.currency,
        status: "draft",
        notes: body.notes,
        created_at: "2026-04-10T10:00:00Z",
      };
      invoiceRows = [created, ...invoiceRows];
      return Promise.resolve(okJson(created));
    }

    if (path === "/invoices/17/status") {
      const body = JSON.parse(String(options?.body || "{}"));
      invoiceRows = invoiceRows.map((invoice) =>
        invoice.id === 17 ? { ...invoice, status: body.status } : invoice
      );
      return Promise.resolve(okJson({ ok: true }));
    }

    throw new Error(`Unexpected apiFetch call: ${path}`);
  });
}

describe("Supplier payouts page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    payoutRows = [
      {
        id: 101,
        amount: 320,
        status: "completed",
        method: "bank",
        reference: "SUP-REF-101",
        notes: "Primary batch",
        created_at: "2026-04-01T08:00:00Z",
        processed_at: "2026-04-02T09:00:00Z",
      },
      {
        id: 102,
        amount: 140,
        status: "processing",
        method: "bank",
        reference: "SUP-REF-102",
        notes: "Awaiting transfer",
        created_at: "2026-04-03T08:00:00Z",
        processed_at: null,
      },
    ];
    invoiceRows = [
      {
        id: 17,
        invoice_number: "INV-20260328-ABCD1234",
        order_id: 42,
        total_amount: "149.5",
        currency: "AED",
        status: "issued",
        created_at: "2026-03-28T10:00:00Z",
        due_date: "2026-04-15T00:00:00Z",
      },
    ];
    wireApiFetch();
  });

  it("filters payout history and shows expandable detail rows", async () => {
    render(<SupplierPayoutsPage />);

    await screen.findByText("Payout history");

    fireEvent.change(screen.getByPlaceholderText("Search id, reference, notes"), {
      target: { value: "SUP-REF-102" },
    });

    await waitFor(() => {
      expect(screen.getByText("SUP-REF-102")).toBeInTheDocument();
      expect(screen.queryByText("SUP-REF-101")).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Show detail"));

    expect(screen.getByText("Awaiting transfer")).toBeInTheDocument();
    expect(screen.getByText("Bank Transfer")).toBeInTheDocument();
  });

  it("surfaces invoice records inside the payouts workspace and creates new invoice entries", async () => {
    render(<SupplierPayoutsPage />);

    await screen.findByText("Payout history");

    fireEvent.click(screen.getByRole("button", { name: /invoice records/i }));

    await screen.findByText("Invoice history");
    expect(screen.getByText("INV-20260328-ABCD1234")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("Order number"), {
      target: { value: "42" },
    });
    fireEvent.change(screen.getByPlaceholderText("Optional shipment id"), {
      target: { value: "7" },
    });
    fireEvent.change(screen.getByPlaceholderText("Optional invoice note"), {
      target: { value: "Packed and ready for pickup" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create invoice record/i }));

    await waitFor(() => {
      const createCall = mockApiFetch.mock.calls.find(([path]) => path === "/invoices/");
      expect(createCall).toBeTruthy();
      expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
        order_id: 42,
        shipment_id: 7,
        currency: "AED",
        notes: "Packed and ready for pickup",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("INV-NEW")).toBeInTheDocument();
    });
  });
});


