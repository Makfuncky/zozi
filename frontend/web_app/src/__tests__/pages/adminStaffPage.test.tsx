import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockApiFetch = jest.fn();

let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;
let mockSection = "staff";

const staffDirectory = [
  {
    id: 7,
    username: "ops_staff",
    full_name: "Ops Staff",
    email: "ops@zozi.test",
    phone: "+96812345678",
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
    staff_notes: "Covers the late shift.",
    created_at: "2026-04-06T00:00:00Z",
  },
  {
    id: 8,
    username: "mod_staff",
    full_name: "Moderation Staff",
    email: "moderation@zozi.test",
    phone: "+96887654321",
    role: "moderator",
    is_active: false,
    staff_role_label: "Fraud Review Lead",
    staff_title: "Moderator",
    staff_department: "Trust & Safety",
    staff_area_of_operation: "Fraud Desk",
    staff_hire_date: "2025-09-01",
    staff_experience_level: "Senior",
    staff_performance_summary: "Escalation specialist",
    staff_assigned_tasks: ["Fraud review"],
    staff_assigned_projects: ["Chargeback audit"],
    permissions: ["audit.read", "staff.view"],
    staff_notes: null,
    created_at: "2026-04-07T00:00:00Z",
  },
];

const permissionCatalog = {
  groups: [
    { key: "users", label: "Users & Staff", permissions: ["users.read", "staff.view", "staff.manage", "staff.delete"] },
    { key: "ops", label: "Operations", permissions: ["audit.read", "tickets.manage"] },
  ],
  defaults: {
    admin: ["users.read", "staff.view", "staff.manage", "staff.delete"],
    sub_admin: ["users.read", "staff.view"],
    moderator: ["audit.read", "staff.view"],
    support: ["audit.read", "tickets.manage", "staff.view"],
  },
};

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: jest.fn() }),
  useSearchParams: () => ({ get: (key: string) => (key === "section" ? mockSection : null) }),
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

jest.mock("@shared/adminPermissions", () => ({
  ADMIN_PERMISSION_MAP: {
    admin: ["users.read", "staff.view", "staff.manage", "staff.delete"],
    sub_admin: ["users.read", "staff.view"],
    moderator: ["audit.read", "staff.view"],
    support: ["audit.read", "tickets.manage", "staff.view"],
  },
  STAFF_PERMISSION_GROUPS: [
    { key: "users", label: "Users & Staff", permissions: ["users.read", "staff.view", "staff.manage", "staff.delete"] },
    { key: "ops", label: "Operations", permissions: ["audit.read", "tickets.manage"] },
  ],
  hasAdminPermission: jest.fn(() => true),
  isAdminStaffRole: jest.fn(() => true),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => <div data-testid="admin-layout">{title ? <h1>{title}</h1> : null}{children}</div>,
}));

jest.mock("@/app/admin/dashboard/tabs/HierarchyTab", () => ({
  __esModule: true,
  default: () => <div>Hierarchy permissions</div>,
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "compact", setDensity: jest.fn() }),
  dc: (_d: any, compact: any, _normal: any, _expanded: any) => compact,
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: ({ rows, columns, rowActions, selectedRowKeys, onSelectedRowKeysChange, toolbarSlot }: any) => (
    <div>
      {toolbarSlot}
      <table>
        <tbody>
          {(rows ?? []).map((row: any, i: number) => (
            <tr key={i}>
              <td>
                <input
                  type="checkbox"
                  aria-label={`Select row ${row.id}`}
                  checked={(selectedRowKeys ?? []).includes(row.id)}
                  onChange={() => {
                    const current: any[] = selectedRowKeys ?? [];
                    const next = current.includes(row.id)
                      ? current.filter((k: any) => k !== row.id)
                      : [...current, row.id];
                    onSelectedRowKeysChange?.(next);
                  }}
                />
              </td>
              {(columns ?? []).map((col: any) => (
                <td key={col.key}>{col.render ? col.render(row) : String(row[col.key] ?? "")}</td>
              ))}
              {rowActions && <td>{rowActions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ),
}));

import StaffPage from "@/app/admin/staff/page";

describe("Admin staff page", () => {
  beforeEach(() => {
    mockUser = { id: 1, username: "admin", email: "admin@zozi.test", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    mockSection = "staff";
    mockPush.mockReset();
    mockReplace.mockReset();
    mockApiFetch.mockReset();
    mockApiFetch.mockImplementation(async (input: string, init?: RequestInit) => {
      if (input === "/admin/staff") {
        return okJson(staffDirectory);
      }
      if (input === "/admin/staff/permission-catalog") {
        return okJson(permissionCatalog);
      }
      if (input === "/admin/staff/bulk" && init?.method === "PUT") {
        return okJson({
          updated_users: [
            {
              ...staffDirectory[0],
              staff_department: "Trust & Safety",
            },
          ],
        });
      }
      return okJson({});
    });
  });

  it("loads the enterprise staff directory and opens the profile view", async () => {
    render(<StaffPage />);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/staff");
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/staff/permission-catalog");
    });

    expect(await screen.findByText("Staff Directory")).toBeInTheDocument();
    expect(screen.getAllByText("Ops Staff").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Moderation Staff").length).toBeGreaterThan(0);

    fireEvent.click(screen.getAllByRole("button", { name: "View" })[0]);

    expect(await screen.findByText("Staff Profile")).toBeInTheDocument();
    expect(screen.getAllByText("Returns Shift Lead").length).toBeGreaterThan(0);
    expect(screen.getByText("Covers the late shift.")).toBeInTheDocument();
  });

  it("opens the bulk update modal from grid selection and submits updates", async () => {
    render(<StaffPage />);

    expect(await screen.findByText("Staff Directory")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Select row 7"));

    expect(await screen.findByTestId("bulk-action-bar")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Bulk Update" }));

    expect(await screen.findByText("Bulk Update Staff")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Department"), { target: { value: "Trust & Safety" } });
    fireEvent.click(screen.getByRole("button", { name: "Update 1 Staff" }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/staff/bulk",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({
            user_ids: [7],
            updates: { staff_department: "Trust & Safety" },
          }),
        })
      );
    });

    expect(await screen.findByText("Updated 1 staff accounts.")).toBeInTheDocument();
    expect(screen.queryByTestId("bulk-action-bar")).not.toBeInTheDocument();
  });

  it("filters the grid by role and status using the enterprise toolbar controls", async () => {
    render(<StaffPage />);

    expect(await screen.findByText("Staff Directory")).toBeInTheDocument();

    fireEvent.change(screen.getByDisplayValue("All roles"), { target: { value: "support" } });
    fireEvent.change(screen.getByDisplayValue("All statuses"), { target: { value: "active" } });

    await waitFor(() => {
      expect(screen.getAllByText("Ops Staff").length).toBeGreaterThan(0);
    });
    expect(screen.queryByText("Moderation Staff")).not.toBeInTheDocument();
   });
 });


