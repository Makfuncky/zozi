import React from "react";
import { render, screen } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockReplace = jest.fn();
const mockPush = jest.fn();
const mockUseSearchParams = jest.fn(() => new URLSearchParams("section=returns"));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, push: mockPush }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ user: { id: 17, username: "supplier" }, isLoading: false }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => unknown) =>
    selector({ format: (value: number) => `OMR ${value.toFixed(2)}` }),
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "normal" }),
  dc: (_density: string, _compact: string, regular: string, _expanded: string) => regular,
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector: (state: { addToast: jest.Mock }) => unknown) => selector({ addToast: jest.fn() }),
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

jest.mock("@/components/BrandLoading", () => ({
  __esModule: true,
  default: ({ label }: { label: string }) => <div>{label}</div>,
}));

jest.mock("@/components/QuickDetailModal", () => ({
  __esModule: true,
  default: ({ children, open }: any) => (open ? <div>{children}</div> : null),
}));

jest.mock("@/lib/utils", () => ({
  cn: (...values: Array<string | false | null | undefined>) => values.filter(Boolean).join(" "),
  resolveImage: (value: string) => value,
}));

jest.mock("@shared/trackingMap", () => ({
  buildTrackingMapHref: () => "#",
  extractTrackingMapPoints: () => [],
}));

import SupplierOrdersWorkspacePage from "@/app/supplier/orders/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Supplier orders page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(new URLSearchParams("section=returns"));
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/supplier/orders?")) {
        return Promise.resolve(okJson({ data: [], total: 0, page: 1, pageSize: 20 }));
      }

      if (path === "/logistics/summary") {
        return Promise.resolve(
          okJson({
            awaiting_fulfilment: 0,
            in_transit: 0,
            delivered_total: 0,
            total_shipments: 0,
            pending_shipments: 0,
            active_zones: 0,
          })
        );
      }

      throw new Error(`Unexpected apiFetch call: ${path}`);
    });
  });

  it("highlights the merged returns workflow when opened from the retired returns route", async () => {
    render(<SupplierOrdersWorkspacePage />);

    await screen.findByText("Returns are handled from orders");

    expect(
      screen.getByText(
        "Delivered orders with return activity stay anchored to the original order record."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Manage handoffs, shipments, delivery confirmations, and return-linked order follow-up from one workspace."
      )
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Back to all orders" })).toBeInTheDocument();
  });
});


