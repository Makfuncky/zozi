import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
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

jest.mock("nanoid", () => ({
  nanoid: () => "mock-nanoid",
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isAdminAlertRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: (refresh: () => void | Promise<void>) => ({
    cancel: jest.fn(),
    trigger: () => {
      void refresh();
    },
  }),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/admin/EmailCampaignManager", () => ({
  __esModule: true,
  default: () => <div>Email campaign manager</div>,
}));

jest.mock("@/components/admin/EmailTemplateManager", () => ({
  __esModule: true,
  default: () => <div>Email template manager</div>,
}));

jest.mock("framer-motion", () => ({
  motion: {
    tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

import AdminUsersPage from "@/app/admin/users/page";
import AdminAuditLogsPage from "@/app/admin/audit-logs/page";
import AdminEmailDashboard from "@/app/admin/email/page";
import AdminBannersPage from "@/app/admin/banners/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("Admin management web pages", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    mockApiFetch.mockReset();
    mockPush.mockReset();
    mockReplace.mockReset();
  });

  it("redirects support users away from the user-management page", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("allows sub-admin users to load the user-management page", async () => {
    mockUser = { id: 2, username: "subadmin", email: "subadmin@zozi.test", role: "sub_admin" };
    mockApiFetch.mockResolvedValue(okJson([
      {
        id: 11,
        username: "customer-one",
        email: "customer-one@zozi.test",
        role: "customer",
        is_active: true,
        is_verified: true,
        created_at: "2026-03-29T09:00:00",
      },
    ]));

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/users?limit=500&offset=0");
    });

    expect(await screen.findByPlaceholderText("Search user ID, name, email, role, or login activity...")).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalledWith("/admin/login");
  });

  it("continues loading user pages when backend pagination metadata omits total", async () => {
    const firstPage = Array.from({ length: 500 }, (_, index) => ({
      id: index + 1,
      username: `user-${index + 1}`,
      email: `user-${index + 1}@zozi.test`,
      role: "customer",
      is_active: true,
      is_verified: false,
      email_verified: true,
      created_at: "2026-03-29T09:00:00",
    }));

    mockApiFetch
      .mockResolvedValueOnce(okJson({ data: firstPage, pageSize: 500, page: 1 }))
      .mockResolvedValueOnce(okJson([
        {
          id: 501,
          username: "user-501",
          email: "user-501@zozi.test",
          role: "customer",
          is_active: true,
          is_verified: false,
          email_verified: true,
          created_at: "2026-03-29T09:00:00",
        },
      ]));

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenNthCalledWith(1, "/admin/users?limit=500&offset=0");
      expect(mockApiFetch).toHaveBeenNthCalledWith(2, "/admin/users?limit=500&offset=500");
    });

    fireEvent.change(screen.getByPlaceholderText("Search user ID, name, email, role, or login activity..."), {
      target: { value: "user-501" },
    });

    expect((await screen.findAllByText("user-501")).length).toBeGreaterThan(0);
  });

  it("lets admins reset a user password from the user management page", async () => {
    mockApiFetch
      .mockResolvedValueOnce(okJson([
        {
          id: 11,
          username: "customer-one",
          email: "customer-one@zozi.test",
          role: "customer",
          is_active: true,
          is_verified: true,
          email_verified: true,
          created_at: "2026-03-29T09:00:00",
        },
      ]))
      .mockResolvedValueOnce(okJson({ message: "Password reset for user 'customer-one'" }));

    render(<AdminUsersPage />);

    await screen.findByPlaceholderText("Search user ID, name, email, role, or login activity...");

    fireEvent.click((await screen.findAllByLabelText("Reset password for customer-one"))[0]);
    fireEvent.change(screen.getByPlaceholderText("New password (min 6 chars)"), { target: { value: "ResetPass123!" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/users/11/reset-password",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ new_password: "ResetPass123!" }),
        }),
      );
    });
  });

  it("allows support users to read audit logs", async () => {
    mockUser = { id: 7, username: "support", email: "support@zozi.test", role: "support" };
    mockApiFetch.mockResolvedValueOnce(okJson({
      items: [
        {
          id: 91,
          username: "support",
          user_role: "support",
          action: "USER_ACTIVE_TOGGLED",
          resource_type: "user",
          resource_id: 11,
          details: { is_active: false },
          status: "success",
          created_at: "2026-03-29T10:00:00",
        },
      ],
      total: 1,
      page: 1,
      page_size: 30,
      total_pages: 1,
    }));

    render(<AdminAuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("USER_ACTIVE_TOGGLED")).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalledWith("/admin/login");
    expect(mockApiFetch).toHaveBeenCalledWith("/admin/audit-logs?page=1&page_size=30");
  });

  it("redirects sub-admin users away from the email dashboard", async () => {
    mockUser = { id: 2, username: "subadmin", email: "subadmin@zozi.test", role: "sub_admin" };

    render(<AdminEmailDashboard />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/login");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("redirects sub-admin users away from banner management", async () => {
    mockUser = { id: 2, username: "subadmin", email: "subadmin@zozi.test", role: "sub_admin" };

    render(<AdminBannersPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/admin/promotions?section=banners");
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});


