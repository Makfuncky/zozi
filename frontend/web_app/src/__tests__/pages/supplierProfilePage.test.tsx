import React from "react";
import { render, screen } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockReplace = jest.fn();
const mockPush = jest.fn();
const mockRefresh = jest.fn();
const mockUseSearchParams = jest.fn(() => new URLSearchParams());

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: mockPush, prefetch: jest.fn() }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
  },
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getErrorMessage: () => "Request failed",
  parseJsonResponse: async (response: { json: () => Promise<unknown> }) => response.json(),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: { id: 7, username: "supplier", email: "supplier@zozi.com" },
    refresh: mockRefresh,
    isLoading: false,
  }),
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

jest.mock("@/lib/utils", () => ({
  resolveImage: (value: string) => value,
  supplierStorefrontPath: () => "/suppliers/supplier",
}));

import SupplierProfilePage from "@/app/supplier/profile/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

function notFoundJson() {
  return {
    ok: false,
    json: async () => ({}),
  };
}

describe("Supplier profile page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockApiFetch.mockImplementation((path: string) => {
      if (path === "/supplier/products") {
        return Promise.resolve(okJson([]));
      }

      if (path === "/supplier/profile/business") {
        return Promise.resolve(
          okJson({
            business_name: "Acme Trading",
            business_type: "company",
            verification_status: "approved",
            certifications: [],
            social_links: {},
          })
        );
      }

      if (path === "/supplier-documents/my") {
        return Promise.resolve(okJson([]));
      }

      if (path === "/supplier/regions") {
        return Promise.resolve(okJson({ origin_country: "Oman", city: "Muscat", operating_regions: [] }));
      }

      if (path === "/supplier/bank-account") {
        return Promise.resolve(
          okJson({
            id: 11,
            beneficiary_name: "Acme Trading",
            bank_name: "Bank Muscat",
            currency: "OMR",
            verification_status: "verified",
          })
        );
      }

      if (path.startsWith("/suppliers/resolve/")) {
        return Promise.resolve(notFoundJson());
      }

      throw new Error(`Unexpected apiFetch call: ${path}`);
    });
  });

  it("opens the documents workspace when the merged profile route receives tab=documents", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("tab=documents"));

    render(<SupplierProfilePage />);

    expect(await screen.findByText("KYC workspace")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No KYC documents uploaded yet. Add your business registration and compliance files here before requesting review."
      )
    ).toBeInTheDocument();
  });

  it("opens the guide workspace when the merged profile route receives tab=guide", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("tab=guide"));

    render(<SupplierProfilePage />);

    expect(await screen.findByText("Supplier guide")).toBeInTheDocument();
    expect(screen.getByText("Detailed walkthrough")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open full supplier guide/i })).toHaveAttribute("href", "#full-guide");
  });

  it("normalizes the legacy payout tab onto the bank workspace", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("tab=payout"));

    render(<SupplierProfilePage />);

    expect(await screen.findByText("Bank account used for supplier settlements")).toBeInTheDocument();
    expect(screen.getByText("Payout bank details")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open payouts workspace/i })).toBeInTheDocument();
  });
});


