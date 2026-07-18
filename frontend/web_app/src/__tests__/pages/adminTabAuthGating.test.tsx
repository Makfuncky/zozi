import React from "react";
import { render, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
let currentAuthState: Record<string, unknown>;

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => currentAuthState,
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "compact", setDensity: jest.fn() }),
  dc: (_d: any, compact: any) => compact,
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (value: string) => value,
}));

jest.mock("@/components/TranslatedText", () => ({
  __esModule: true,
  default: ({ text }: { text: string }) => <>{text}</>,
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => unknown) => selector({ format: (value: number) => `AED ${value.toFixed(2)}` }),
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: () => <div>table</div>,
}));

import LogisticsTab from "@/app/admin/dashboard/tabs/LogisticsTab";
import PayoutsTab from "@/app/admin/dashboard/tabs/PayoutsTab";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin tab auth gating", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    currentAuthState = { user: null, isLoggedIn: false, isLoading: true };

    mockApiFetch.mockImplementation(async (path: string) => {
      if (path === "/logistics/summary") return okJson({ total_shipments: 0, awaiting_fulfilment: 0, in_transit: 0, delivered_total: 0, active_zones: 0 });
      if (path === "/logistics/distribution/channels") return okJson([]);
      if (path === "/logistics/shipments/active") return okJson([]);
      if (path === "/logistics/carriers") return okJson([]);
      if (path === "/logistics/zones") return okJson([]);
      if (path === "/admin/payouts/pending") return okJson([]);
      if (path === "/finance/admin/supplier-settlements?status=eligible&limit=100") return okJson([]);
      throw new Error(`Unhandled request ${path}`);
    });
  });

  it("waits for auth hydration before loading logistics data", async () => {
    const { rerender } = render(<LogisticsTab />);

    expect(mockApiFetch).not.toHaveBeenCalled();

    currentAuthState = { user: { id: 1, role: "admin", username: "admin" }, isLoggedIn: true, isLoading: false };
    rerender(<LogisticsTab />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics/summary");
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics/distribution/channels");
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics/shipments/active");
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics/carriers");
      expect(mockApiFetch).toHaveBeenCalledWith("/logistics/zones");
    });
  });

  it("waits for auth hydration before loading payouts data", async () => {
    const { rerender } = render(<PayoutsTab />);

    expect(mockApiFetch).not.toHaveBeenCalled();

    currentAuthState = { user: { id: 1, role: "admin", username: "admin" }, isLoggedIn: true, isLoading: false };
    rerender(<PayoutsTab />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/payouts/pending");
      expect(mockApiFetch).toHaveBeenCalledWith("/finance/admin/supplier-settlements?status=eligible&limit=100");
    });
  });
});


