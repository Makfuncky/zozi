import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { isAdminStaffRole } from "@shared/adminPermissions";

const mockPush = jest.fn();
const mockReplace = jest.fn();
let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;
const mockApiFetch = jest.fn((input: string) => {
  if (input === "/admin/staff") {
    return Promise.resolve({
      ok: true,
      json: async () => [
        {
          id: 7,
          username: "ops_staff",
          full_name: "Ops Staff",
          email: "ops@zozi.test",
          phone: null,
          role: "support",
          is_active: true,
          staff_role_label: "Returns Shift Lead",
          staff_title: "Support Agent",
          staff_department: "Support",
          staff_area_of_operation: "Returns Desk",
          staff_hire_date: "2026-01-15",
          staff_experience_level: "Mid-level",
          staff_performance_summary: "Reliable",
          staff_assigned_tasks: ["Returns triage"],
          staff_assigned_projects: ["CSAT uplift"],
          permissions: ["audit.read", "tickets.manage", "staff.view"],
          staff_notes: null,
          created_at: "2026-04-06T00:00:00Z",
        },
      ],
    });
  }
  if (input === "/admin/staff/permission-catalog") {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        groups: [
          { key: "users", label: "Users & Staff", permissions: ["users.read", "staff.view", "staff.manage", "staff.delete"] },
        ],
        defaults: {
          admin: ["users.read", "staff.view", "staff.manage", "staff.delete"],
          sub_admin: ["users.read", "staff.view"],
          moderator: ["audit.read", "staff.view"],
          support: ["audit.read", "tickets.manage", "staff.view"],
        },
      }),
    });
  }
  return Promise.resolve({ ok: true, json: async () => [] });
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
  useSearchParams: () => ({ get: () => null }),
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
  apiFetch: (input: string) => mockApiFetch(input),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => selector({ locale: "en" }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) => selector({ format: (v: number) => `AED ${v.toFixed(2)}` }),
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text: string) => text,
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isAdminAlertRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@shared/adminPermissions", () => ({
  ADMIN_PERMISSION_MAP: {
    admin: ["analytics.view", "users.read", "staff.view", "staff.manage", "staff.delete"],
    sub_admin: ["analytics.view", "users.read", "staff.view"],
    moderator: ["audit.read", "staff.view"],
    support: ["audit.read", "tickets.manage", "staff.view"],
  },
  STAFF_PERMISSION_GROUPS: [
    { key: "users", label: "Users & Staff", permissions: ["users.read", "staff.view", "staff.manage", "staff.delete"] },
  ],
  hasAdminPermission: jest.fn(() => true),
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
  default: ({ children, title }: any) => <div data-testid="admin-layout">{title && <h1>{title}</h1>}{children}</div>,
}));

jest.mock("framer-motion", () => ({
  motion: { div: ({ children, ...props }: any) => <div {...props}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock tab components so they render identifiable text
jest.mock("@/app/admin/dashboard/tabs/FinanceTab", () => ({ __esModule: true, default: () => <div>FinanceTab content</div> }));
jest.mock("@/app/admin/dashboard/tabs/ModerationTab", () => ({ __esModule: true, default: () => <div>ModerationTab content</div> }));
jest.mock("@/app/admin/dashboard/tabs/TicketsTab", () => ({ __esModule: true, default: () => <div>TicketsTab content</div> }));
jest.mock("@/app/admin/dashboard/tabs/PayoutsTab", () => ({ __esModule: true, default: () => <div>PayoutsTab content</div> }));
jest.mock("@/app/admin/dashboard/tabs/SupplierDocumentsTab", () => ({ __esModule: true, default: () => <div>SupplierDocumentsTab content</div> }));
jest.mock("@/app/admin/dashboard/tabs/HierarchyTab", () => ({ __esModule: true, default: () => <div>HierarchyTab content</div> }));

import FinancePage from "@/app/admin/finance/page";
import StaffPage from "@/app/admin/staff/page";
import ModerationPage from "@/app/admin/moderation/page";
import TicketsPage from "@/app/admin/tickets/page";

describe("Standalone admin pages", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin", permissions: ["users.read", "staff.view", "staff.manage", "staff.delete"] };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("renders Finance page with FinanceTab", async () => {
    render(<FinancePage />);
    await waitFor(() => {
      expect(screen.getAllByText("Finance & Cash Management").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("FinanceTab content")).toBeInTheDocument();
    expect(screen.getByTestId("admin-layout")).toBeInTheDocument();
  });

  it("renders Staff page with staff heading", async () => {
    render(<StaffPage />);
    await waitFor(() => {
      expect(screen.getByText("Staff Management")).toBeInTheDocument();
    });
    expect(screen.getByTestId("admin-layout")).toBeInTheDocument();
  });

  it("redirects the Moderation standalone page to the Resolution Center", async () => {
    render(<ModerationPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/resolution?section=moderation");
    });
  });

  it("redirects the Tickets standalone page to the Resolution Center", async () => {
    render(<TicketsPage />);
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/resolution?section=tickets");
    });
  });

  it("redirects unauthenticated user to login on Finance page", async () => {
    mockIsLoggedIn = false;
    mockUser = null;

    render(<FinancePage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });
  });

  it("redirects non-staff user to login on Staff page", async () => {
    (isAdminStaffRole as unknown as jest.Mock).mockReturnValue(false);
    mockUser = { id: 2, username: "customer", role: "customer" };

    render(<StaffPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });
  });
});


