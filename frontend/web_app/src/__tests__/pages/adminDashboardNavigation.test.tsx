import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockHasAdminPermission = jest.fn((role: string | null | undefined, permission: string) => true);
const mockRouter = { push: mockPush, replace: mockReplace, prefetch: jest.fn() };

let mockTab: string | null = null;
let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;

jest.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => ({ get: (key: string) => (key === "tab" ? mockTab : null) }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
    logout: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: (state: { locale: string }) => string) => selector({ locale: "en" }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: (state: { format: (value: number) => string }) => string | ((value: number) => string)) =>
    selector({ format: (value: number) => `AED ${value.toFixed(2)}` }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text: string) => text,
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isAdminAlertRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@shared/adminPermissions", () => ({
  hasAdminPermission: (role: string | null | undefined, permission: string) =>
    mockHasAdminPermission(role, permission),
  isAdminStaffRole: jest.fn(() => true),
}));

jest.mock("@shared/localization", () => ({
  isRtlLocale: jest.fn(() => false),
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: jest.fn(() => ({ trigger: jest.fn(), cancel: jest.fn() })),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/TranslatedText", () => ({
  __esModule: true,
  default: ({ text }: { text: string }) => <>{text}</>,
}));

jest.mock("@/app/admin/dashboard/tabs/InsightsTab", () => ({ __esModule: true, default: () => <div>Insights tab</div> }));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

import AdminDashboardPage from "@/app/admin/dashboard/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin dashboard navigation", () => {
  beforeEach(() => {
    mockTab = null;
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
    mockHasAdminPermission.mockImplementation(() => true);
    mockApiFetch
      .mockResolvedValueOnce(okJson({ total_users: 12, total_suppliers: 4, total_products: 88, total_orders: 27, total_revenue: 9100 }));
  });

  it("renders overview workspaces on the base dashboard route", async () => {
    render(<AdminDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Primary Workspaces")).toBeInTheDocument();
    });

    expect(screen.getByText("Operational Hubs")).toBeInTheDocument();
    expect(screen.getByText("Command Center")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("redirects legacy duplicate tabs to their standalone pages", async () => {
    mockTab = "analytics";

    render(<AdminDashboardPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/command-center");
    });

    expect(screen.getByText("Opening the consolidated workspace for this admin area...")).toBeInTheDocument();
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("redirects the legacy suppliers dashboard tab to the standalone suppliers page", async () => {
    mockTab = "suppliers";

    render(<AdminDashboardPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/suppliers");
    });

    expect(screen.getByText("Opening the consolidated workspace for this admin area...")).toBeInTheDocument();
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("hides featured workspaces the active role cannot access", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };
    mockHasAdminPermission.mockImplementation((role: string | null | undefined, permission: string) => {
      if (role !== "support") {
        return false;
      }
      return permission === "analytics.view" || permission === "tickets.manage" || permission === "orders.manage";
    });

    render(<AdminDashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Primary Workspaces")).toBeInTheDocument();
    });

    expect(screen.getByText("Command Center")).toBeInTheDocument();
    expect(screen.queryByText("Email")).not.toBeInTheDocument();
    expect(screen.queryByText("Finance")).not.toBeInTheDocument();
  });

  it.each([
    ["finance", "/admin/finance"],
    ["staff", "/admin/staff"],
    ["moderation", "/admin/moderation"],
    ["tickets", "/admin/tickets"],
    ["payouts", "/admin/finance?section=payouts"],
    ["supplier-documents", "/admin/suppliers?section=documents"],
    ["logistics", "/admin/logistics"],
    ["hierarchy", "/admin/staff?section=permissions"],
    ["compare", "/admin/suppliers?section=compare"],
    ["coupons", "/admin/promotions?section=coupons"],
    ["flash-sales", "/admin/promotions?section=flash-sales"],
    ["banner", "/admin/promotions?section=banners"],
    ["logistics-partners", "/admin/logistics?section=partners"],
  ])("redirects legacy %s tab to %s", async (tabKey, expectedRoute) => {
    mockTab = tabKey;

    render(<AdminDashboardPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(expectedRoute);
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});


