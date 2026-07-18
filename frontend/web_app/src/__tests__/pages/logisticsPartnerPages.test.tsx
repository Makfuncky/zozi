import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();

jest.mock("@/lib/api", () => ({
  API_URL: "http://localhost:8000",
  getAccessToken: jest.fn(() => null),
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

jest.mock("@/components/LogisticsPartnerLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/SignaturePad", () => ({
  __esModule: true,
  default: ({ onChange }: any) => (
    <button type="button" onClick={() => onChange("data:image/png;base64,mock-signature")}>Mock Sign</button>
  ),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
  },
}));

jest.mock("nanoid", () => ({
  nanoid: () => "mock-nanoid",
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: { id: 5, username: "fastship", email: "lp@zozi.test", role: "logistics_partner" },
    isLoggedIn: true,
    isLoading: false,
    logout: jest.fn(),
  }),
}));

import LogisticsPartnerDashboardPage from "@/app/logistics-partner/dashboard/page";
import LogisticsPartnerProfilePage from "@/app/logistics-partner/profile/page";
import LogisticsPartnerScanPage from "@/app/logistics-partner/scan/page";
import LogisticsPartnerShipmentsPage from "@/app/logistics-partner/shipments/page";
import LogisticsPartnerPayoutsPage from "@/app/logistics-partner/payouts/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Logistics partner web pages", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
    mockPush.mockReset();
    window.history.pushState({}, "", "/");
  });

  it("renders analytics metrics on the dashboard", async () => {
    mockApiFetch.mockResolvedValueOnce(okJson({
      stats: { total: 12, active: 4, delivered: 6, pending: 1, failed: 1 },
      analytics: {
        delivery_rate: 50,
        average_transit_hours: 7.5,
        scan_compliance_rate: 91.7,
        sla_on_time_rate: 88.9,
        shipments_with_events: 11,
        sla_eligible_shipments: 9,
        status_breakdown: {
          pending: 1,
          processing: 0,
          shipped: 2,
          in_transit: 2,
          delivered: 6,
          failed: 1,
          returned: 0,
        },
      },
      channel_breakdown: { express: 5, ground: 7 },
      active_shipments: [],
      live_locations: [],
      route_plan: {
        generated_at: null,
        total_stops: 0,
        estimated_distance_km: 0,
        estimated_duration_hours: 0,
        stops: [],
      },
      sla_alerts: [],
      payout_summary: {
        total_earned: 0,
        available_balance: 0,
        pending_amount: 0,
        completed_amount: 0,
        payout_count: 0,
        recent_payouts: [],
      },
    }));

    render(<LogisticsPartnerDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("50.0%")).toBeInTheDocument();
    });

    expect(screen.getByText("7.5h")).toBeInTheDocument();
    expect(screen.getByText("91.7%")).toBeInTheDocument();
    expect(screen.getByText("88.9%")).toBeInTheDocument();
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partner/dashboard");
  });

  it("renders the logistics profile workspace and accepts terms", async () => {
    let acceptedTerms = false;
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/profile" && !options) {
        return okJson({
          id: 5,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          city: "Dubai",
          country: "UAE",
          bio: "City-wide deliveries.",
          verification_status: "pending",
          verification_note: "Awaiting admin review",
          status: "pending_onboarding",
          is_terms_accepted: acceptedTerms,
          service_types: ["express"],
        });
      }
      if (path === "/logistics-partner/service-areas" && !options) {
        return okJson([
          {
            id: 12,
            partner_id: 5,
            country_code: "AE",
            country_name: "United Arab Emirates",
            city_name: "Dubai",
            charge_amount: 18,
            currency: "AED",
            is_active: true,
            approval_status: "pending",
            review_note: "Awaiting admin review",
          },
        ]);
      }
      if (path === "/logistics-partner/me/bank-account" && !options) {
        return okJson({});
      }
      if (path === "/logistics-partner/profile/terms/accept" && options?.method === "POST") {
        acceptedTerms = true;
        return okJson({ detail: "Terms accepted", terms_version: "2026-04" });
      }
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerProfilePage />);

    await waitFor(() => {
      expect(screen.getAllByText("pending onboarding").length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText("pending onboarding").length).toBeGreaterThan(0);
    expect(screen.getByText("One-page partner operations")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Operations & Compliance"));
    fireEvent.click(screen.getByText("Accept logistics terms"));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partner/profile/terms/accept", expect.objectContaining({ method: "POST" }));
    });
  });

  it("shows only the supported category fee inputs in delivery settings", async () => {
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partner/profile") {
        return okJson({
          id: 5,
          name: "FastShip Logistics",
          code: "FASTSHIP",
          city: "Dubai",
          country: "UAE",
          verification_status: "pending",
          status: "pending_onboarding",
          is_terms_accepted: false,
        });
      }
      if (path === "/logistics-partner/service-areas") return okJson([]);
      if (path === "/logistics-partner/pricing-profiles") return okJson([]);
      if (path === "/logistics-partner/category-rules") return okJson([]);
      if (path === "/logistics-partner/vehicle-rules") return okJson([]);
      if (path === "/logistics-partner/me/bank-account") return okJson({});
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerProfilePage />);

    await waitFor(() => {
      expect(screen.getAllByText("pending onboarding").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByText("Delivery Settings"));

    await waitFor(() => {
      expect(screen.getByText("Handling Rule Submission")).toBeInTheDocument();
    });

    expect(screen.getByText("Highest handling amount")).toBeInTheDocument();
    expect(screen.getByText("Handling amount")).toBeInTheDocument();
    expect(screen.queryByText("Per kg override")).not.toBeInTheDocument();
    expect(screen.queryByText("Fragile multiplier")).not.toBeInTheDocument();
  });

  it("renders safely when optional logistics dashboard collections are missing", async () => {
    mockApiFetch.mockResolvedValueOnce(okJson({
      stats: { total: 3, active: 1, delivered: 1, pending: 1, failed: 0 },
      analytics: {
        delivery_rate: 33.3,
        average_transit_hours: 2.5,
        scan_compliance_rate: 50,
        sla_on_time_rate: 100,
      },
    }));

    render(<LogisticsPartnerDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("33.3%")).toBeInTheDocument();
    });

    expect(screen.getByText("0 live pings")).toBeInTheDocument();
    expect(screen.getByText("No GPS checkpoints have been received yet for active shipments.")).toBeInTheDocument();
  });

  it("loads the shipment list and refetches when the status filter changes", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson({
        total: 1,
        page: 1,
        page_size: 30,
        total_pages: 1,
        items: [
          {
            id: 17,
            order_id: 71,
            tracking_number: "TRACK-LP-001",
            carrier_name: "Aramex",
            status: "in_transit",
            current_hub: "Dubai South",
            scan_code: "SHIP-17",
            shipping_address: "Business Bay, Dubai",
            estimated_delivery: "2026-03-29T10:00:00",
          },
        ],
      }))
      .mockResolvedValueOnce(okJson({
        total: 1,
        page: 1,
        page_size: 30,
        total_pages: 1,
        items: [
          {
            id: 18,
            order_id: 72,
            tracking_number: "TRACK-LP-002",
            carrier_name: "DHL",
            status: "delivered",
            current_hub: "Abu Dhabi",
            scan_code: "SHIP-18",
            shipping_address: "Corniche, Abu Dhabi",
            estimated_delivery: "2026-03-29T10:00:00",
          },
        ],
      }));

    render(<LogisticsPartnerShipmentsPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/TRACK-LP-001/).length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getByDisplayValue("All Statuses"), {
      target: { value: "delivered" },
    });

    await waitFor(() => {
      expect(screen.getAllByText(/TRACK-LP-002/).length).toBeGreaterThan(0);
    });

    expect(mockApiFetch).toHaveBeenNthCalledWith(1, "/logistics-partner/shipments?page=1&page_size=30");
    expect(mockApiFetch).toHaveBeenNthCalledWith(2, "/logistics-partner/shipments?page=1&page_size=30&status=delivered");
  });

  it("accepts prepared pickup directly from the shipment row", async () => {
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/shipments?page=1&page_size=30" && !options) {
        return okJson({
          total: 1,
          page: 1,
          page_size: 30,
          total_pages: 1,
          items: [
            {
              id: 44,
              order_id: 91,
              status: "prepared",
              status_label: "Prepared",
              tracking_number: "SHIP-44",
              scan_code: "SHIP-44",
              supplier_pickup_address: "Supplier Warehouse, Muscat",
              customer_dropoff_address: "Ruwi, Muscat",
              estimated_partner_payout: 3.5,
            },
          ],
        });
      }
      if (path === "/logistics-partner/shipments/44/status" && options?.method === "PUT") {
        return okJson({
          id: 44,
          status: "picking_up",
          status_label: "Picking Up",
        });
      }
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerShipmentsPage />);

    await waitFor(() => {
      expect(screen.getAllByLabelText("Pickup action for order 91")[0]).toHaveValue("picking_up");
    });

    fireEvent.click(screen.getAllByText("Confirm")[0]);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partner/shipments/44/status",
        expect.objectContaining({ method: "PUT" }),
      );
    });

    const statusCall = mockApiFetch.mock.calls.find((call) => call[0] === "/logistics-partner/shipments/44/status");
    const statusBody = JSON.parse(String(statusCall?.[1]?.body));
    expect(statusBody).toMatchObject({ status: "picking_up", event_type: "pickup_confirmed", load_fit_label: "car" });
  });

  it("shows the accepted vehicle lock and pricing guardrails on shipment rows", async () => {
    mockApiFetch.mockResolvedValueOnce(okJson({
      total: 1,
      page: 1,
      page_size: 30,
      total_pages: 1,
      items: [
        {
          id: 55,
          order_id: 104,
          tracking_number: "SHIP-55",
          scan_code: "SHIP-55",
          status: "picking_up",
          accepted_load_fit_label: "van",
          accepted_load_fit_factor: 1.2,
          accepted_shipping_amount: 24,
          accepted_vehicle_selected_at: "2026-03-29T10:00:00Z",
          estimated_partner_payout: 14,
          pricing_breakdown: {
            shipping_amount: 24,
            pickup_fee: 2,
            dropoff_fee: 3,
            ceiling_applied: true,
          },
        },
      ],
    }));

    render(<LogisticsPartnerShipmentsPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/Load-fit lock: Van x1\.20/).length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText(/Locked route charge:/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Stops: pickup/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Max cap").length).toBeGreaterThan(0);
  });

  it("shows receive via scan for picking_up rows and does not allow direct shipped transition inline", async () => {
    mockApiFetch.mockResolvedValueOnce(okJson({
      total: 1,
      page: 1,
      page_size: 30,
      total_pages: 1,
      items: [
        {
          id: 19,
          order_id: 73,
          tracking_number: "SHIP-3",
          carrier_name: "Local Courier",
          status: "picking_up",
          current_hub: "ST 4111, Al khuwair, Muscat",
          scan_code: "SHIP-3",
          shipping_address: "Babylene, Al Khuwair, Muscat, 112, OMAN",
        },
      ],
    }));

    render(<LogisticsPartnerShipmentsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Receive via Scan").length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText("Manage Pickup").length).toBeGreaterThan(0);
    expect(screen.queryByText("Mark Shipped")).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByText("Manage Pickup")[0]);

    const statusSelect = await screen.findByDisplayValue("prepared") as HTMLSelectElement;
    expect(Array.from(statusSelect.options).map((option) => option.value)).toEqual(["prepared"]);
  });

  it("auto-lookups the shipment when scan page opens with a code query param", async () => {
    window.history.pushState({}, "", "/logistics-partner/scan?code=ORDER-73");
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics-partner/shipments/scan?code=ORDER-73") {
        return okJson({
          id: 19,
          order_id: 73,
          status: "picking_up",
          status_label: "picking up",
          tracking_number: "SHIP-3",
          scan_code: "SHIP-3",
          current_hub: "ST 4111, Al khuwair, Muscat",
          shipping_address: "Babylene, Al Khuwair, Muscat, 112, OMAN",
        });
      }
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerScanPage />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partner/shipments/scan?code=ORDER-73");
    });

    expect(await screen.findByText("Shipment #19")).toBeInTheDocument();
    expect(screen.getByDisplayValue("ORDER-73")).toBeInTheDocument();
  });

  it("requires a customer signature before confirming delivered on the web scan flow", async () => {
    window.history.pushState({}, "", "/logistics-partner/scan?code=SHIP-19");
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/shipments/scan?code=SHIP-19") {
        return okJson({
          id: 19,
          order_id: 73,
          status: "in_transit",
          status_label: "Out for Delivery",
          tracking_number: "TRK-DEL-019",
          scan_code: "SHIP-19",
          current_hub: "Palm Jumeirah",
          shipping_address: "Dubai Marina",
          customer_name: "Amina Customer",
          customer_phone: "+971500000000",
        });
      }
      if (path === "/logistics-partner/shipments/19/confirmation-request" && options?.method === "POST") {
        return okJson({
          shipment_id: 19,
          order_id: 73,
          status: "in_transit",
          status_label: "Out for Delivery",
          request: {
            id: 301,
            shipment_id: 19,
            order_id: 73,
            supplier_id: 11,
            confirmation_type: "delivery",
            confirmation_type_label: "Delivery Confirmation",
            status: "pending",
            requested_status: "delivered",
            current_hub: "Palm Jumeirah",
            tracking_number: "TRK-DEL-019",
            delivery_signature_name: "Amina Customer",
            delivery_signature_data_url: "data:image/png;base64,mock-signature",
            created_at: "2026-03-30T12:00:00Z",
            target_role: "customer",
            target_user_id: 22,
          },
        });
      }
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerScanPage />);

    await waitFor(() => {
      expect(screen.getByText("Shipment #19")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delivered" }));
    fireEvent.click(screen.getByRole("button", { name: "Send Confirmation Request" }));

    expect(await screen.findByText("Customer name and signature are required to confirm delivery.")).toBeInTheDocument();
    expect(mockApiFetch).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Mock Sign" }));
    fireEvent.change(screen.getByPlaceholderText("Customer full name"), {
      target: { value: "Amina Customer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Confirmation Request" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledTimes(2);
    });

    const [, requestOptions] = mockApiFetch.mock.calls[1];
    const body = JSON.parse(String(requestOptions.body));
    expect(body).toMatchObject({
      requested_status: "delivered",
      event_type: "customer_received",
      tracking_number: "TRK-DEL-019",
      scan_code: "SHIP-19",
      delivery_signature_name: "Amina Customer",
      delivery_signature_data_url: "data:image/png;base64,mock-signature",
    });

    expect(await screen.findByText("Confirmation request sent. Status will update after approval.")).toBeInTheDocument();
  });

  it("loads payout history and submits a payout request", async () => {
    let requestSubmitted = false;
    mockApiFetch.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/logistics-partner/dashboard") {
        return okJson({
          payout_summary: requestSubmitted
            ? {
                total_earned: 980,
                available_balance: 170,
                pending_amount: 200,
                completed_amount: 610,
                payout_count: 3,
              }
            : {
                total_earned: 980,
                available_balance: 320,
                pending_amount: 50,
                completed_amount: 610,
                payout_count: 2,
              },
        });
      }
      if (path === "/logistics-partner/payouts") {
        return okJson(requestSubmitted
          ? [
              {
                id: 5,
                amount: 150,
                status: "pending",
                method: "bank",
                notes: "Shift closeout",
                created_at: "2026-03-30T10:00:00",
              },
            ]
          : [
              {
                id: 4,
                amount: 125,
                status: "pending",
                method: "bank",
                notes: "Weekly settlement",
                created_at: "2026-03-29T10:00:00",
              },
            ]);
      }
      if (path === "/logistics-partner/payouts/request" && options?.method === "POST") {
        requestSubmitted = true;
        return okJson({ id: 5, amount: 150, status: "pending" });
      }
      throw new Error(`Unexpected path ${path}`);
    });

    render(<LogisticsPartnerPayoutsPage />);

    await waitFor(() => {
      expect(screen.getByText("Payout history")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText("150.00"), { target: { value: "150" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit request" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/logistics-partner/payouts/request",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
  });
});


