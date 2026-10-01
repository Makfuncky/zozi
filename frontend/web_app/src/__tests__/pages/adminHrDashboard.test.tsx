import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

const mockPush = jest.fn();
const mockReplace = jest.fn();

let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;
const mockApiFetch = jest.fn((input: string) => {
  if (input === "/hr/dashboard?days=7") {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        onboarding: {
          stats: { active: 0, overdue: 0, completed: 0, cancelled: 0 },
          overdue_items: [],
        },
        performance: {
          stats: { green: 0, amber: 0, red: 0, not_scored: 0, avg_score: null },
          top_performers: [],
          bottom_performers: [],
        },
        activity: {
          total_events: 0,
          action_breakdown: {},
          events: [],
        },
        employees: { total: 0, active: 0, terminating: 0, terminated: 0 },
      }),
    });
  }
  return Promise.resolve({ ok: false, json: async () => ({}) });
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
  useSearchParams: () => ({ get: () => null }),
  usePathname: () => "/admin/hr",
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
}));

jest.mock("@/lib/useAdminCountry", () => ({
  useAdminCountry: () => ({ selectedCountry: null }),
}));

jest.mock("@shared/adminPermissions", () => ({
  isAdminStaffRole: jest.fn(() => true),
  hasAdminPermission: jest.fn(() => true),
}));

jest.mock("framer-motion", () => ({
  motion: { div: ({ children, ...props }: any) => <div {...props}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock("@/lib/icons", () => ({
  Users: () => <div>UsersIcon</div>,
  Activity: () => <div>ActivityIcon</div>,
  TrendingUp: () => <div>TrendingUpIcon</div>,
  AlertCircle: () => <div>AlertCircleIcon</div>,
  CheckCircle2: () => <div>CheckCircle2Icon</div>,
  Clock: () => <div>ClockIcon</div>,
  ArrowRight: () => <div>ArrowRightIcon</div>,
  Loader2: () => <div>Loader2Icon</div>,
  RefreshCw: () => <div>RefreshCwIcon</div>,
  Calendar: () => <div>CalendarIcon</div>,
  UserPlus: () => <div>UserPlusIcon</div>,
  UserX: () => <div>UserXIcon</div>,
  BarChart3: () => <div>BarChart3Icon</div>,
  Star: () => <div>StarIcon</div>,
  Award: () => <div>AwardIcon</div>,
  Zap: () => <div>ZapIcon</div>,
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => <div data-testid="admin-layout">{title && <h1>{title}</h1>}{children}</div>,
}));

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

jest.mock("@/components/ui/StatCard", () => ({
  __esModule: true,
  StatCard: ({ label, value, sub, icon: Icon }: any) => (
    <div data-testid="stat-card">
      {label}: {value} {sub && <span data-testid="stat-sub">{sub}</span>}
    </div>
  ),
}));

import HrDashboardPage from "@/app/admin/hr/page";

describe("HR Dashboard page", () => {
  beforeEach(() => {
    mockUser = {
      id: 1,
      username: "admin",
      email: "admin@zozi.test",
      role: "admin",
      permissions: ["hr.read"],
    };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("renders the dashboard when user has hr.read permission", async () => {
    render(<HrDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Onboarding pipeline, performance health, and recent activity")).toBeInTheDocument();
    });
  });

  it("blocks access when user lacks hr.read permission", async () => {
    const { hasAdminPermission } = require("@shared/adminPermissions");
    hasAdminPermission.mockReturnValue(false);

    render(<HrDashboardPage />);
    await waitFor(() => {
      expect(screen.queryByText("Onboarding Pipeline")).not.toBeInTheDocument();
    });
  });

  it("uses hasAdminPermission for auth gating instead of isAdminStaffRole", async () => {
    const { hasAdminPermission, isAdminStaffRole } = require("@shared/adminPermissions");
    hasAdminPermission.mockReturnValue(true);
    isAdminStaffRole.mockReturnValue(true);

    render(<HrDashboardPage />);
    await waitFor(() => {
      expect(hasAdminPermission).toHaveBeenCalledWith(expect.any(String), "hr.read");
    });
  });
});
