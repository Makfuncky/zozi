import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockAddToast = jest.fn();
const mockReplace = jest.fn();
const mockUseSearchParams = jest.fn(() => new URLSearchParams());

let ticketRows: Array<Record<string, unknown>> = [];
let disputeRows: Array<Record<string, unknown>> = [];

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: (state: { addToast: typeof mockAddToast }) => unknown) => selector({ addToast: mockAddToast }),
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

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children }: any) => <div>{children}</div>,
}));

import SupplierSupportPage from "@/app/supplier/support/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

function wireApiFetch() {
  mockApiFetch.mockImplementation((path: string, options?: { body?: string }) => {
    if (path === "/tickets") {
      if (!options) {
        return Promise.resolve(okJson(ticketRows));
      }
      const body = JSON.parse(String(options.body || "{}"));
      const created = {
        id: 77,
        subject: body.subject,
        status: "open",
        priority: body.priority,
        created_at: "2026-04-11T09:00:00Z",
      };
      ticketRows = [created, ...ticketRows];
      return Promise.resolve(okJson(created));
    }

    if (path === "/supplier/disputes") {
      if (!options) {
        return Promise.resolve(okJson({ data: disputeRows }));
      }
      const body = JSON.parse(String(options.body || "{}"));
      const created = {
        id: 305,
        dispute_type: body.dispute_type,
        priority: body.priority,
        status: "pending",
        title: body.title || "Untitled dispute",
        description: body.description,
        related_order_id: body.related_order_id ?? null,
        created_at: "2026-04-12T09:00:00Z",
      };
      disputeRows = [created, ...disputeRows];
      return Promise.resolve(okJson(created));
    }

    throw new Error(`Unexpected apiFetch call: ${path}`);
  });
}

describe("SupplierSupportPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    ticketRows = [
      {
        id: 18,
        subject: "Billing help",
        status: "open",
        priority: "normal",
        created_at: "2026-04-01T10:00:00Z",
        reply_count: 2,
      },
    ];
    disputeRows = [
      {
        id: 45,
        dispute_type: "payout",
        priority: "high",
        status: "under_review",
        title: "Order payout mismatch",
        description: "Settlement amount does not match the delivered order total.",
        related_order_id: 991,
        created_at: "2026-04-02T10:00:00Z",
      },
    ];
    wireApiFetch();
  });

  it("supports the redirected dispute section query and renders dispute cases in the merged workspace", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("section=disputes"));

    render(<SupplierSupportPage />);

    await screen.findByText("Dispute cases");
    await waitFor(() => {
      expect(screen.getByText(/Order payout mismatch/i)).toBeInTheDocument();
      expect(screen.getByText(/Related order #991/i)).toBeInTheDocument();
    });
  });

  it("submits supplier support tickets through the merged support workspace", async () => {
    render(<SupplierSupportPage />);

    await screen.findByText("Ticket history");

    fireEvent.change(screen.getByPlaceholderText("Brief description of the issue"), {
      target: { value: "Need access to payout statement" },
    });
    fireEvent.change(screen.getByPlaceholderText("Describe what happened and what you need from admin."), {
      target: { value: "Please share the finance breakdown for the last completed transfer." },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit support request/i }));

    await waitFor(() => {
      const createCall = mockApiFetch.mock.calls.find(([path, options]) => path === "/tickets" && options?.method === "POST");
      expect(createCall).toBeTruthy();
      expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
        subject: "Need access to payout statement",
        message: "Please share the finance breakdown for the last completed transfer.",
        priority: "normal",
      });
    });

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Support request submitted", "success");
      expect(screen.getByText(/Need access to payout statement/i)).toBeInTheDocument();
    });
  });
});


