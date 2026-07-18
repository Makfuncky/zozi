import {
  buildAdminAuditLogsQuery,
  buildAdminEmailCampaignPayload,
  normalizeAdminAuditLogPage,
  normalizeAdminUsers,
} from "@/lib/adminManagementUtils";

describe("admin management mobile helpers", () => {
  it("normalizes admin user payloads from backend user records", () => {
    const users = normalizeAdminUsers([
      {
        id: 12,
        username: "ops_admin",
        email: "ops@zozi.test",
        role: "sub_admin",
        is_active: 1,
        created_at: "2026-03-29T10:00:00",
      },
      {
        id: 13,
        full_name: "Support Agent",
        email: "support@zozi.test",
        role: "support",
        is_active: 0,
        created_at: "2026-03-29T11:00:00",
      },
    ]);

    expect(users).toEqual([
      {
        id: 12,
        username: "ops_admin",
        display_name: "ops_admin",
        email: "ops@zozi.test",
        role: "sub_admin",
        is_active: true,
        created_at: "2026-03-29T10:00:00",
        total_orders: undefined,
      },
      {
        id: 13,
        username: "support@zozi.test",
        display_name: "Support Agent",
        email: "support@zozi.test",
        role: "support",
        is_active: false,
        created_at: "2026-03-29T11:00:00",
        total_orders: undefined,
      },
    ]);
  });

  it("builds the audit log query with page pagination parameters", () => {
    expect(buildAdminAuditLogsQuery(3, 30)).toBe("/admin/audit-logs?page=3&page_size=30");
  });

  it("normalizes paginated admin audit log responses", () => {
    const page = normalizeAdminAuditLogPage({
      items: [{ id: 1, user_id: 7, action: "USER_ACTIVE_TOGGLED", status: "success", created_at: "2026-03-29T12:00:00" }],
      total: 4,
      page: 2,
      page_size: 1,
      total_pages: 4,
    });

    expect(page.items).toHaveLength(1);
    expect(page.total).toBe(4);
    expect(page.page).toBe(2);
    expect(page.total_pages).toBe(4);
  });

  it("builds a valid admin email campaign create payload", () => {
    expect(buildAdminEmailCampaignPayload("  Flash Update ", " <p>Live now</p> ", "newsletter")).toEqual({
      name: "Flash Update",
      subject: "Flash Update",
      html_content: "<p>Live now</p>",
      recipients: "newsletter",
      status: "draft",
    });
  });
});