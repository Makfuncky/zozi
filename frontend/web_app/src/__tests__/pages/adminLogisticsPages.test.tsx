import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
  },
}));

import AdminInvoicesPage from "@/app/admin/invoices/page";
import AdminLogisticsPage from "@/app/admin/logistics/page";
import AdminLogisticsPartnersPage from "@/app/admin/logistics/LogisticsPartnersPanel";
import AdminProductVerificationPage from "@/app/admin/product-verification/page";
import AdminReturnsPage from "@/app/admin/returns/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

function getPartnerTable() {
  return screen.getByRole("table");
}

function getPartnerRow(partnerName: string) {
  const row = within(getPartnerTable()).getAllByText(partnerName)[0]?.closest("tr");
  if (!row) {
    throw new Error(`Could not find table row for ${partnerName}`);
  }
  return row;
}

describe("Admin logistics web pages", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("renders invoices from the shared paginated invoice route and refetches with filters", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson({
        total: 2,
        page: 1,
        page_size: 100,
        total_pages: 1,
        items: [
          {
            id: 12,
            invoice_number: "INV-20260329-ADMIN1",
            supplier_id: 1,
            supplier_name: "Test Supplier",
            amount: 130,
            currency: "AED",
            issued_date: "2026-03-29T09:00:00",
            due_date: "2026-04-29T09:00:00",
            status: "pending",
          },
          {
            id: 13,
            invoice_number: "INV-20260329-ADMIN2",
            supplier_id: 2,
            supplier_name: "Other Supplier",
            amount: 155,
            currency: "AED",
            issued_date: "2026-03-29T10:00:00",
            due_date: "2026-04-29T10:00:00",
            status: "approved",
          },
        ],
      }));

    render(<AdminInvoicesPage />);

    await waitFor(() => {
      expect(screen.getByText("INV-20260329-ADMIN1")).toBeInTheDocument();
    });

    expect(screen.getByText("INV-20260329-ADMIN2")).toBeInTheDocument();

    // Client-side filter via the status select dropdown
    fireEvent.change(screen.getByDisplayValue("All statuses"), { target: { value: "approved" } });

    // After filtering, only the approved invoice should be visible
    expect(screen.queryByText("INV-20260329-ADMIN1")).not.toBeInTheDocument();
    expect(screen.getByText("INV-20260329-ADMIN2")).toBeInTheDocument();

    // Only one fetch call (no re-fetch on filter change)
    expect(mockApiFetch).toHaveBeenCalledTimes(1);
    expect(mockApiFetch).toHaveBeenCalledWith("/invoices/");
  });

  it("allows support users to read invoices without management controls", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };
    mockApiFetch.mockResolvedValueOnce(okJson({
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
      items: [
        {
          id: 77,
          invoice_number: "INV-SUPPORT-77",
          supplier_id: 5,
          supplier_name: "Support Supplier",
          amount: 90,
          currency: "AED",
          issued_date: "2026-03-29T12:00:00",
          due_date: "2026-04-29T12:00:00",
          status: "pending",
        },
      ],
    }));

    render(<AdminInvoicesPage />);

    await waitFor(() => {
      expect(screen.getByText("INV-SUPPORT-77")).toBeInTheDocument();
    });

    expect(screen.queryByText("Create Invoice from Order")).not.toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalledWith("/admin/login");
  });

  it("renders logistics partners from the shared partner management route", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partners/") return okJson([
        {
          id: 9,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          contact_email: "ops@fastship.test",
          status: "active",
          verification_status: "under_review",
          verification_note: "Awaiting admin review",
          country: "UAE",
          city: "Dubai",
          coverage_regions: ["Dubai", "Abu Dhabi"],
          service_types: ["standard", "express"],
          created_at: "2026-03-29T08:00:00",
        },
      ]);
      if (path === "/logistics-partners/service-areas") return okJson([
        {
          id: 11,
          partner_id: 9,
          country_code: "AE",
          country_name: "United Arab Emirates",
          city_name: "Dubai",
          charge_amount: 18,
          currency: "AED",
          is_active: true,
          approval_status: "pending",
        },
      ]);
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    // Switch to the Partners workspace tab
    await waitFor(() => expect(screen.getByRole("button", { name: /Partners/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Partners/ }));

    await waitFor(() => {
      expect(screen.getAllByText("FastShip Logistics")[0]).toBeInTheDocument();
    });

    const partnerTable = getPartnerTable();
    const partnerRow = getPartnerRow("FastShip Logistics");

    expect(within(partnerTable).getAllByText("FASTSHIP").length).toBeGreaterThan(0);
    expect(within(partnerTable).getByText("Dubai, UAE")).toBeInTheDocument();
    expect(within(partnerRow).getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/");
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/service-areas");
  });

  it("renders the compact logistics workspace tabs with coverage as the default section", async () => {
    render(<AdminLogisticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Coverage first, one simple charge model second")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /^Coverage & Routes$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Cost Drivers$/i })).toBeInTheDocument();
    expect(screen.getByText("Coverage first, one simple charge model second")).toBeInTheDocument();
    expect(screen.getByText("Partner registry and service-area review")).toBeInTheDocument();
  });

  it("renders the simplified pricing review flow in the cost drivers workspace", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partners/") {
        return okJson([
          {
            id: 9,
            name: "FastShip Logistics",
            code: "FASTSHIP",
            contact_email: "ops@fastship.test",
            status: "active",
            verification_status: "approved",
            created_at: "2026-03-29T08:00:00",
          },
        ]);
      }
      if (path === "/logistics-partners/service-areas") {
        return okJson([
          {
            id: 11,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Dubai",
            zone_label: "Dubai Marina",
            charge_amount: 18,
            currency: "AED",
            is_active: true,
            approval_status: "approved",
          },
        ]);
      }
      if (path === "/logistics-partners/pricing-profiles") {
        return okJson([
          {
            id: 21,
            partner_id: 9,
            service_area_id: 11,
            profile_name: "Dubai Marina Default",
            currency: "AED",
            approval_status: "approved",
            is_active: true,
          },
        ]);
      }
      if (path === "/logistics-partners/category-rules") return okJson([]);
      if (path === "/logistics-partners/vehicle-rules") return okJson([]);
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage scope="pricing" />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /zozi logistics pricing control/i })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Partner"), { target: { value: "9" } });
    fireEvent.change(screen.getByLabelText("Service Area"), { target: { value: "11" } });

    await waitFor(() => {
      expect(screen.getByText("Handling Rule Review Queue")).toBeInTheDocument();
    });

    expect(screen.getByText("Handling Rule Review Queue")).toBeInTheDocument();
    expect(screen.getByText(/extra stop charges/i)).toBeInTheDocument();
    expect(screen.getAllByText("Dubai Marina").length).toBeGreaterThan(0);
    expect(mockApiFetch).not.toHaveBeenCalledWith(expect.stringContaining("/logistics-partners/pricing-insights?partner_id=9"));
  });

  it("uses the highest approved handling rule in the pricing preview", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partners/") {
        return okJson([
          {
            id: 9,
            name: "FastShip Logistics",
            code: "FASTSHIP",
            contact_email: "ops@fastship.test",
            status: "active",
            verification_status: "approved",
            created_at: "2026-03-29T08:00:00",
          },
        ]);
      }
      if (path === "/logistics-partners/service-areas") {
        return okJson([
          {
            id: 11,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Dubai",
            zone_label: "Dubai Marina",
            charge_amount: 18,
            pickup_charge: 1.5,
            dropoff_charge: 1.5,
            per_kg_rate: 2,
            currency: "AED",
            is_active: true,
            approval_status: "approved",
          },
        ]);
      }
      if (path === "/logistics-partners/pricing-profiles") {
        return okJson([
          {
            id: 21,
            partner_id: 9,
            service_area_id: 11,
            profile_name: "Dubai Marina Default",
            base_in_city_fee: 12,
            per_kg_rate: 2,
            fuel_multiplier: 1,
            currency: "AED",
            approval_status: "approved",
            is_active: true,
          },
        ]);
      }
      if (path === "/logistics-partners/category-rules") {
        return okJson([
          {
            id: 31,
            partner_id: 9,
            service_area_id: 11,
            category_name: "Fragile Electronics",
            flat_fee_override: 4,
            special_handling_fee: 3,
            currency: "AED",
            approval_status: "approved",
            is_active: true,
          },
          {
            id: 32,
            partner_id: 9,
            service_area_id: 11,
            category_name: "Cold Chain",
            flat_fee_override: 6,
            special_handling_fee: 5,
            currency: "AED",
            approval_status: "approved",
            is_active: true,
          },
        ]);
      }
      if (path === "/logistics-partners/vehicle-rules") return okJson([]);
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage scope="pricing" />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /zozi logistics pricing control/i })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Partner"), { target: { value: "9" } });
    fireEvent.change(screen.getByLabelText("Service Area"), { target: { value: "11" } });

    const calculatorSectionHeading = await screen.findByText(/test the weight-first formula/i);
    const calculatorSection = calculatorSectionHeading.closest("section");
    if (!calculatorSection) {
      throw new Error("Could not find the pricing preview section");
    }

    await waitFor(() => {
      expect(within(calculatorSection).getByText(/highest rule: cold chain/i)).toBeInTheDocument();
    });

    expect(screen.getByText("Applied Handling Rule")).toBeInTheDocument();
    expect(screen.getByText(/highest rule: cold chain/i)).toBeInTheDocument();
    expect(screen.getAllByText("6.00 AED").length).toBeGreaterThan(0);
  });

  it("approves a logistics partner profile from the admin review queue", async () => {
    let approved = false;
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partners/" && !options) {
        return okJson([{
          id: 9,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          contact_email: "ops@fastship.test",
          status: approved ? "active" : "pending_onboarding",
          verification_status: approved ? "approved" : "under_review",
          verification_note: approved ? "Approved" : "Awaiting admin review",
          country: "UAE",
          city: "Dubai",
          coverage_regions: ["Dubai"],
          service_types: ["express"],
          created_at: "2026-03-29T08:00:00",
        }]);
      }
      if (path === "/logistics-partners/review/profile/9" && options?.method === "POST") {
        approved = true;
        return okJson({ id: 9, verification_status: "approved", status: "active" });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Partners/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Partners/ }));

    await waitFor(() => {
      expect(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });

    fireEvent.click(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Approve" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partners/review/profile/9",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("preserves pickup and dropoff stop fees when editing a service area", async () => {
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partners/" && !options) {
        return okJson([
          {
            id: 9,
            name: "FastShip Logistics",
            code: "FASTSHIP",
            contact_email: "ops@fastship.test",
            status: "active",
            verification_status: "approved",
            created_at: "2026-03-29T08:00:00",
          },
        ]);
      }
      if (path === "/logistics-partners/service-areas" && !options) {
        return okJson([
          {
            id: 11,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Dubai",
            charge_amount: 18,
            pickup_charge: 4,
            dropoff_charge: 6,
            currency: "AED",
            is_active: true,
            approval_status: "pending",
          },
        ]);
      }
      if (path === "/logistics-partners/service-areas/11" && options?.method === "PUT") {
        return okJson({ id: 11 });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Service Areas/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Service Areas/ }));

    await waitFor(() => {
      expect(screen.getByText(/pickup 4\.00\/stop/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Edit"));
    fireEvent.click(screen.getByText("Update Area"));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partners/service-areas/11",
        expect.objectContaining({ method: "PUT" }),
      );
    });

    const updateCall = mockApiFetch.mock.calls.find((call) => call[0] === "/logistics-partners/service-areas/11");
    const requestBody = JSON.parse(String(updateCall?.[1]?.body));
    expect(requestBody.pickup_charge).toBe(4);
    expect(requestBody.dropoff_charge).toBe(6);
  });

  it("renders the coverage and route board with unresolved coordinate warnings", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partners/") {
        return okJson([
          {
            id: 9,
            name: "FastShip Logistics",
            code: "FASTSHIP",
            contact_email: "ops@fastship.test",
            status: "active",
            verification_status: "approved",
            created_at: "2026-03-29T08:00:00",
          },
        ]);
      }
      if (path === "/logistics-partners/service-areas") {
        return okJson([
          {
            id: 11,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Dubai",
            zone_label: "Dubai Marina",
            latitude: 25.0801,
            longitude: 55.1403,
            charge_amount: 18,
            currency: "AED",
            is_active: true,
            approval_status: "approved",
          },
          {
            id: 12,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Abu Dhabi",
            zone_label: "Airport Zone",
            latitude: 24.4539,
            longitude: 54.3773,
            charge_amount: 25,
            currency: "AED",
            is_active: true,
            approval_status: "approved",
          },
          {
            id: 13,
            partner_id: 9,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Sharjah",
            zone_label: "Warehouse Zone",
            charge_amount: 16,
            currency: "AED",
            is_active: true,
            approval_status: "pending",
          },
        ]);
      }
      if (path === "/logistics-partners/pricing-profiles") return okJson([]);
      if (path === "/logistics-partners/category-rules") return okJson([]);
      if (path === "/logistics-partners/vehicle-rules") return okJson([]);
      if (path === "/logistics-partners/city-distances") {
        return okJson({
          items: [
            {
              id: 71,
              origin_country_code: "AE",
              origin_city_name: "Dubai",
              destination_country_code: "AE",
              destination_city_name: "Abu Dhabi",
              distance_km: 139,
              notes: "Primary corridor",
            },
            {
              id: 72,
              origin_country_code: "AE",
              origin_city_name: "Sharjah",
              destination_country_code: "AE",
              destination_city_name: "Abu Dhabi",
              distance_km: 162,
              notes: "Needs Sharjah coordinates",
            },
          ],
        });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Service Areas/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Service Areas/ }));

    await waitFor(() => {
      expect(screen.getByText("Coverage and Route Board")).toBeInTheDocument();
    });

    expect(screen.getAllByText("Dubai to Abu Dhabi").length).toBeGreaterThan(0);
    expect(screen.getByText("Rows that still need coordinates")).toBeInTheDocument();
    expect(screen.getAllByText("Sharjah to Abu Dhabi").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Missing service-area latitude or longitude.").length).toBeGreaterThan(0);
  });

  it("shows only the supported category fee controls in the admin logistics form", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partners/") {
        return okJson([
          {
            id: 9,
            name: "FastShip Logistics",
            code: "FASTSHIP",
            contact_email: "ops@fastship.test",
            status: "active",
            verification_status: "approved",
            created_at: "2026-03-29T08:00:00",
          },
        ]);
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Handling Rules/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Handling Rules/ }));
    fireEvent.click(screen.getByText("New Handling Rule"));

    expect(screen.getByText("Handling Amount")).toBeInTheDocument();
    expect(screen.queryByText("Legacy Flat Fee")).not.toBeInTheDocument();
    expect(screen.queryByText("Per kg Override")).not.toBeInTheDocument();
    expect(screen.queryByText("Fragile Multiplier")).not.toBeInTheDocument();
  });

  it("toggles a logistics partner portal status from the standalone page", async () => {
    let suspended = false;
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partners/" && !options) {
        return okJson([{
          id: 9,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          contact_email: "ops@fastship.test",
          status: suspended ? "suspended" : "active",
          verification_status: "approved",
          verification_note: "Approved",
          country: "UAE",
          city: "Dubai",
          coverage_regions: ["Dubai"],
          service_types: ["express"],
          created_at: "2026-03-29T08:00:00",
        }]);
      }
      if (path === "/logistics-partners/9" && options?.method === "PUT") {
        suspended = true;
        return okJson({ id: 9, status: "suspended" });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Partners/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Partners/ }));

    await waitFor(() => {
      expect(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Suspend" })).toBeInTheDocument();
    });

    fireEvent.click(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Suspend" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partners/9",
        expect.objectContaining({ method: "PUT" }),
      );
    });

    const toggleCall = mockApiFetch.mock.calls.find((call) => call[0] === "/logistics-partners/9" && call[1]?.method === "PUT");
    expect(JSON.parse(toggleCall?.[1].body)).toEqual({ status: "suspended" });
  });

  it("deletes a logistics partner from the standalone page", async () => {
    const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);
    let deleted = false;

    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partners/" && !options) {
        return okJson(deleted ? [] : [{
          id: 9,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          contact_email: "ops@fastship.test",
          status: "active",
          verification_status: "approved",
          verification_note: "Approved",
          country: "UAE",
          city: "Dubai",
          coverage_regions: ["Dubai"],
          service_types: ["express"],
          created_at: "2026-03-29T08:00:00",
        }]);
      }
      if (path === "/logistics-partners/9" && options?.method === "DELETE") {
        deleted = true;
        return okJson({ success: true });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Partners/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Partners/ }));

    await waitFor(() => {
      expect(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    fireEvent.click(within(getPartnerRow("FastShip Logistics")).getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/9", { method: "DELETE" });
    });

    confirmSpy.mockRestore();
  });

  it("bulk-approves selected logistics partners from the admin panel", async () => {
    let bulkApproved = false;
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partners/" && !options) {
        if (bulkApproved) {
          return okJson([
            { id: 9, name: "FastShip Logistics", code: "FASTSHIP", contact_email: "ops@fastship.test", status: "active", verification_status: "approved", verification_note: "Approved", country: "UAE", city: "Dubai", coverage_regions: ["Dubai"], service_types: ["express"], created_at: "2026-03-29T08:00:00" },
            { id: 10, name: "BlueRoute Logistics", code: "BLUEROUTE", contact_email: "ops@blueroute.test", status: "active", verification_status: "approved", verification_note: "Approved", country: "UAE", city: "Sharjah", coverage_regions: ["Sharjah"], service_types: ["standard"], created_at: "2026-03-29T08:30:00" },
          ]);
        }
        return okJson([
          { id: 9, name: "FastShip Logistics", code: "FASTSHIP", contact_email: "ops@fastship.test", status: "pending_onboarding", verification_status: "under_review", verification_note: "Awaiting admin review", country: "UAE", city: "Dubai", coverage_regions: ["Dubai"], service_types: ["express"], created_at: "2026-03-29T08:00:00" },
          { id: 10, name: "BlueRoute Logistics", code: "BLUEROUTE", contact_email: "ops@blueroute.test", status: "pending_onboarding", verification_status: "under_review", verification_note: "Awaiting admin review", country: "UAE", city: "Sharjah", coverage_regions: ["Sharjah"], service_types: ["standard"], created_at: "2026-03-29T08:30:00" },
        ]);
      }
      if (path === "/logistics-partners/bulk" && options?.method === "POST") {
        bulkApproved = true;
        return okJson({ action: "approve", processed: 2, skipped: 0, details: [] });
      }
      return okJson([]);
    });

    render(<AdminLogisticsPartnersPage />);

    await waitFor(() => expect(screen.getByRole("button", { name: /Partners/ })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Partners/ }));

    await waitFor(() => {
      expect(within(getPartnerTable()).getByRole("checkbox", { name: "Select row 9" })).toBeInTheDocument();
    });

    fireEvent.click(within(getPartnerTable()).getByRole("checkbox", { name: "Select row 9" }));
    fireEvent.click(within(getPartnerTable()).getByRole("checkbox", { name: "Select row 10" }));
    fireEvent.click(screen.getByRole("button", { name: "Approve Selected" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partners/bulk",
        expect.objectContaining({ method: "POST" }),
      );
    });

    const bulkCall = mockApiFetch.mock.calls.find((call) => call[0] === "/logistics-partners/bulk");
    expect(JSON.parse(bulkCall?.[1].body)).toEqual({ partner_ids: [9, 10], action: "approve" });
  });

  it("redirects product verification page to embedded products section", async () => {
    render(<AdminProductVerificationPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/products?section=verification");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("redirects support users away from product verification management", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };

    render(<AdminProductVerificationPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/products?section=verification");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("redirects all users from standalone returns page to embedded orders section", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };

    const { unmount } = render(<AdminReturnsPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/orders?section=returns");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
    unmount();

    jest.clearAllMocks();
    mockUser = { id: 2, username: "subadmin", email: "subadmin@zozi.test", role: "sub_admin" };

    render(<AdminReturnsPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/orders?section=returns");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});


