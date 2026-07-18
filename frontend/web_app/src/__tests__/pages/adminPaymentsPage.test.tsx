import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockAddToast = jest.fn();

let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  parseJsonResponse: async (response: { json: () => Promise<unknown> }) => response.json(),
  getErrorMessage: (payload: any) => payload?.detail || payload?.message || "Request failed",
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: (state: { addToast: typeof mockAddToast }) => unknown) => selector({ addToast: mockAddToast }),
}));

jest.mock("@shared/adminPermissions", () => ({
  canAccessAdminPaymentManagement: jest.fn(() => true),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="admin-layout">{children}</div>,
}));

import AdminPaymentsPage from "@/app/admin/payments/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin Payments page", () => {
  let runtimeState: any;
  let gatewayState: any[];

  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();

    runtimeState = {
      id: 1,
      online_provider: "stripe",
      source: "database",
      stripe_configured: true,
      tap_configured: true,
      stripe_enabled: true,
      tap_enabled: false,
      enabled_processors: ["stripe"],
      can_accept_online_payments: true,
    };

    gatewayState = [
      {
        id: 1,
        provider_code: "stripe",
        provider_kind: "stripe",
        display_name: "Stripe",
        adapter_supported: true,
        is_enabled: true,
        supports_customer_checkout: true,
        supports_payouts: true,
        mode: "test",
        source: "database",
        public_key: "pk_test_stripe",
        merchant_id: null,
        api_base_url: "https://api.stripe.com",
        webhook_url: "https://api.zozi.test/payments/webhook",
        test_url: "https://api.stripe.com/v1/charges",
        supported_currencies: ["AED", "OMR"],
        extra_config: {},
        notes: "Primary card processor",
        fee_percent: 2.9,
        fixed_fee_amount: 0.3,
        payout_fee_percent: 0,
        payout_fixed_fee_amount: 0,
        pass_fee_to_customer: false,
        settlement_cycle: "daily",
        secret_key_configured: true,
        webhook_secret_configured: true,
        test_status: "passed",
      },
      {
        id: 2,
        provider_code: "paytabs",
        provider_kind: "custom",
        display_name: "PayTabs",
        adapter_supported: true,
        is_enabled: true,
        supports_customer_checkout: true,
        supports_payouts: false,
        mode: "test",
        source: "database",
        public_key: "pub_paytabs",
        merchant_id: "merchant_paytabs",
        api_base_url: "https://secure.paytabs.com",
        webhook_url: "https://api.zozi.test/payments/paytabs/webhook",
        test_url: "https://secure.paytabs.com/payment/query",
        supported_currencies: ["AED", "OMR", "USD"],
        extra_config: {},
        notes: "Hosted checkout",
        fee_percent: 2.5,
        fixed_fee_amount: 0,
        payout_fee_percent: 0,
        payout_fixed_fee_amount: 0,
        pass_fee_to_customer: false,
        settlement_cycle: "weekly",
        secret_key_configured: true,
        webhook_secret_configured: true,
        test_status: "untested",
      },
    ];

    mockApiFetch.mockImplementation((input: string, init?: RequestInit & { disableCache?: boolean }) => {
      if (input === "/payments/config/runtime" && (!init || init.method === undefined)) {
        return Promise.resolve(okJson(runtimeState));
      }
      if (input === "/payments/config/gateways" && (!init || init.method === undefined)) {
        return Promise.resolve(okJson(gatewayState));
      }
      if (input === "/payments/config/runtime" && init?.method === "PUT") {
        const payload = JSON.parse(String(init.body || "{}"));
        runtimeState = { ...runtimeState, online_provider: payload.online_provider, enabled_processors: payload.online_provider === "tap" ? ["tap"] : payload.online_provider === "both" ? ["stripe", "tap"] : ["stripe"] };
        return Promise.resolve(okJson(runtimeState));
      }
      if (input.startsWith("/payments/config/gateways/") && !input.endsWith("/test") && init?.method === "PUT") {
        const providerCode = input.split("/").pop() as string;
        const payload = JSON.parse(String(init.body || "{}"));
        const nextGateway = {
          ...(gatewayState.find((item) => item.provider_code === providerCode) || {}),
          ...payload,
          provider_code: providerCode,
          secret_key_configured: true,
          webhook_secret_configured: true,
          test_status: (gatewayState.find((item) => item.provider_code === providerCode)?.test_status) || "untested",
          source: "database",
          adapter_supported: true,
          extra_config: {},
        };
        gatewayState = [...gatewayState.filter((item) => item.provider_code !== providerCode), nextGateway];
        return Promise.resolve(okJson(nextGateway));
      }
      if (input.endsWith("/test") && init?.method === "POST") {
        const providerCode = input.split("/")[4];
        gatewayState = gatewayState.map((item) => item.provider_code === providerCode ? { ...item, test_status: "passed" } : item);
        return Promise.resolve(okJson({ message: "Gateway test passed" }));
      }
      if (input === "/payments/config/finance-quote" && init?.method === "POST") {
        return Promise.resolve(okJson({
          gateway_code: "stripe",
          gateway_display_name: "Stripe",
          adapter_supported: true,
          order_total: 110,
          gateway_fee_amount: 3.25,
          customer_payable_total: 113.25,
          processor_net_capture: 106.75,
          taxable_product_amount: 100,
          zozi_commission_amount: 10,
          supplier_payout_estimate: 90,
          logistics_payout_estimate: 5,
          estimated_payout_cost: 1,
          platform_net_after_gateway_and_payout_costs: 10.75,
          pass_fee_to_customer: true,
        }));
      }
      return Promise.resolve({ ok: false, json: async () => ({ detail: `Unhandled request ${input}` }) });
    });
  });

  it("redirects unauthenticated users to admin login", async () => {
    mockUser = null;
    mockIsLoggedIn = false;

    render(<AdminPaymentsPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });
  });

  it("loads the payments workspace and saves checkout mode", async () => {
    render(<AdminPaymentsPage />);

    await screen.findByText("Gateway Identity");

    expect(screen.getByLabelText("Display Name")).toHaveValue("Stripe");

    fireEvent.click(screen.getByRole("button", { name: "Tap Only" }));
    fireEvent.click(screen.getByRole("button", { name: "Save Checkout Mode" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/payments/config/runtime", expect.objectContaining({ method: "PUT" }));
    });

    expect(mockAddToast).toHaveBeenCalledWith("Checkout payment mode updated", "success");
  });

  it("saves and tests a gateway configuration", async () => {
    render(<AdminPaymentsPage />);

    await screen.findByText("Gateway Identity");

    const gatewayConnectionsCard = screen.getByText("Gateway Connections").closest(".theme-card") as HTMLElement;
    const payTabsButton = within(gatewayConnectionsCard)
      .getAllByRole("button")
      .find((button) => button.textContent?.includes("PayTabs"));

    expect(payTabsButton).toBeTruthy();
    fireEvent.click(payTabsButton as HTMLButtonElement);

    await waitFor(() => {
      expect(screen.getByLabelText("Display Name")).toHaveValue("PayTabs");
    });

    fireEvent.change(screen.getByLabelText("Display Name"), { target: { value: "PayTabs Hosted Checkout" } });
    fireEvent.click(screen.getByRole("button", { name: "Save and Test" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/payments/config/gateways/paytabs", expect.objectContaining({ method: "PUT" }));
      expect(mockApiFetch).toHaveBeenCalledWith("/payments/config/gateways/paytabs/test", expect.objectContaining({ method: "POST" }));
    });

    expect(mockAddToast).toHaveBeenCalledWith("Gateway test passed", "success");
  });

  it("calculates the payout preview for the selected gateway", async () => {
    render(<AdminPaymentsPage />);

    await screen.findByText("Order to Payout Preview");

    fireEvent.change(screen.getByLabelText("Subtotal"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Shipping"), { target: { value: "5" } });
    fireEvent.change(screen.getByLabelText("VAT"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate Preview" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/payments/config/finance-quote", expect.objectContaining({ method: "POST" }));
    });

    const previewCard = screen.getByText("Preview Result").parentElement as HTMLElement;

    await waitFor(() => {
      expect(within(previewCard).getByText("113.250")).toBeInTheDocument();
    });

    expect(within(previewCard).getByText("10.750")).toBeInTheDocument();
    expect(within(previewCard).getByText("Stripe")).toBeInTheDocument();
  });
});


