import {
  canAccessAdminBannerManagement,
  canAccessAdminEmailManagement,
  canAccessAdminFlashSales,
  canAccessAdminInvoiceManagement,
  canAccessAdminLogisticsPartnerManagement,
  canAccessAdminProductVerification,
  canAccessAdminReturnsManagement,
  canManageAdminInvoices,
  getAdminPermissions,
  hasAdminPermission,
  isAdminStaffRole,
} from "@shared/adminPermissions";

describe("admin permission map", () => {
  it("matches backend user-management boundaries", () => {
    expect(isAdminStaffRole("admin")).toBe(true);
    expect(isAdminStaffRole("customer")).toBe(false);

    expect(hasAdminPermission("admin", "users.delete")).toBe(true);
    expect(hasAdminPermission("sub_admin", "users.toggle_active")).toBe(true);
    expect(hasAdminPermission("sub_admin", "users.delete")).toBe(false);
    expect(hasAdminPermission("moderator", "users.read")).toBe(false);
    expect(hasAdminPermission("support", "users.read")).toBe(false);
  });

  it("keeps audit and hierarchy access available to all staff roles", () => {
    for (const role of ["admin", "sub_admin", "moderator", "support"] as const) {
      expect(hasAdminPermission(role, "audit.read")).toBe(true);
      expect(hasAdminPermission(role, "hierarchy.view")).toBe(true);
      expect(getAdminPermissions(role).length).toBeGreaterThan(0);
    }
  });

  it("matches page-level admin access boundaries", () => {
    expect(canAccessAdminBannerManagement("admin")).toBe(true);
    expect(canAccessAdminBannerManagement("sub_admin")).toBe(false);

    expect(canAccessAdminEmailManagement("admin")).toBe(true);
    expect(canAccessAdminEmailManagement("support")).toBe(false);

    expect(canAccessAdminReturnsManagement("admin")).toBe(true);
    expect(canAccessAdminReturnsManagement("support")).toBe(true);
    expect(canAccessAdminReturnsManagement("sub_admin")).toBe(false);

    expect(canAccessAdminLogisticsPartnerManagement("sub_admin")).toBe(true);
    expect(canAccessAdminLogisticsPartnerManagement("support")).toBe(false);

    expect(canAccessAdminInvoiceManagement("support")).toBe(true);
    expect(canManageAdminInvoices("support")).toBe(false);
    expect(canManageAdminInvoices("sub_admin")).toBe(true);

    expect(canAccessAdminProductVerification("moderator")).toBe(true);
    expect(canAccessAdminProductVerification("support")).toBe(false);

    expect(canAccessAdminFlashSales("admin")).toBe(true);
    expect(canAccessAdminFlashSales("sub_admin")).toBe(false);
  });
});
