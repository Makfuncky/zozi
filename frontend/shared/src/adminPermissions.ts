declare const window: Window & typeof globalThis;

export type AdminStaffRole = "admin" | "sub_admin" | "moderator" | "support" | "country_head" | "country_manager";

export interface StaffPermissionGroup {
  key: string;
  label: string;
  permissions: readonly string[];
}

export const STAFF_PERMISSION_GROUPS: readonly StaffPermissionGroup[] = [
  {
    key: "governance",
    label: "Governance",
    permissions: ["analytics.view", "audit.read", "hierarchy.view"],
  },
  {
    key: "users",
    label: "Users & Staff",
    permissions: [
      "users.read",
      "users.role.update",
      "users.toggle_active",
      "users.delete",
      "users.reset_password",
      "staff.view",
      "staff.create",
      "staff.manage",
      "staff.delete",
    ],
  },
  {
    key: "commerce",
    label: "Commerce Operations",
    permissions: [
      "orders.manage",
      "products.manage",
      "moderation.suppliers",
      "moderation.products",
      "tickets.manage",
      "coupons.manage",
      "payouts.verify",
    ],
  },
  {
    key: "countries",
    label: "Country Management",
    permissions: [
      "countries.configure",
      "countries.payouts",
      "countries.commissions",
      "countries.promotions",
      "countries.finance",
      "countries.banners",
      "countries.email",
    ],
  },
] as const;

export const ADMIN_PERMISSION_MAP: Record<AdminStaffRole, readonly string[]> = {
  admin: [
    "analytics.view",
    "users.read",
    "users.role.update",
    "users.toggle_active",
    "users.delete",
    "users.reset_password",
    "staff.view",
    "staff.create",
    "staff.manage",
    "staff.delete",
    "orders.manage",
    "products.manage",
    "moderation.suppliers",
    "moderation.products",
    "coupons.manage",
    "tickets.manage",
    "audit.read",
    "payouts.verify",
    "hierarchy.view",
  ],
  sub_admin: [
    "users.read",
    "users.toggle_active",
    "staff.view",
    "orders.manage",
    "products.manage",
    "moderation.suppliers",
    "moderation.products",
    "coupons.manage",
    "tickets.manage",
    "audit.read",
    "payouts.verify",
    "hierarchy.view",
  ],
  moderator: [
    "staff.view",
    "products.manage",
    "moderation.suppliers",
    "moderation.products",
    "tickets.manage",
    "audit.read",
    "hierarchy.view",
  ],
  support: [
    "staff.view",
    "orders.manage",
    "tickets.manage",
    "audit.read",
    "hierarchy.view",
  ],
  country_head: [
    "audit.read",
    "staff.view",
    "orders.manage",
    "products.manage",
    "moderation.suppliers",
    "moderation.products",
    "tickets.manage",
    "coupons.manage",
    "payouts.verify",
    "countries.configure",
    "countries.payouts",
    "countries.commissions",
    "countries.promotions",
    "countries.finance",
  ],
  country_manager: [
    "audit.read",
    "staff.view",
    "orders.manage",
    "products.manage",
    "moderation.suppliers",
    "moderation.products",
    "tickets.manage",
    "coupons.manage",
    "countries.promotions",
    "countries.finance",
    "countries.banners",
    "countries.email",
  ],
};

const ADMIN_PERMISSION_OVERRIDE_STORAGE_KEY = "zozi_admin_permission_overrides";
const CURRENT_ADMIN_PERMISSION_STORAGE_KEY = "zozi_current_admin_permissions";

type PermissionOverrideMap = Partial<Record<AdminStaffRole, readonly string[]>>;

let runtimePermissionOverrides: PermissionOverrideMap | null = null;
let runtimeCurrentAdminPermissions: readonly string[] | null = null;

function normalizePermissionOverrideMap(value: unknown): PermissionOverrideMap | null {
  if (!value || typeof value !== "object") return null;

  const normalized: Partial<Record<AdminStaffRole, readonly string[]>> = {};
  for (const role of ["admin", "sub_admin", "moderator", "support", "country_head", "country_manager"] as const) {
    const permissions = (value as Record<string, unknown>)[role];
    if (!Array.isArray(permissions)) continue;
    normalized[role] = permissions
      .map((permission) => String(permission).trim())
      .filter(Boolean);
  }
  return normalized;
}

function readStoredPermissionOverrides(): PermissionOverrideMap | null {
  if (runtimePermissionOverrides) return runtimePermissionOverrides;
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(ADMIN_PERMISSION_OVERRIDE_STORAGE_KEY);
    if (!raw) return null;
    runtimePermissionOverrides = normalizePermissionOverrideMap(JSON.parse(raw));
    return runtimePermissionOverrides;
  } catch {
    return null;
  }
}

function normalizePermissionList(value: unknown): readonly string[] | null {
  if (!Array.isArray(value)) return null;
  return value
    .map((permission) => String(permission).trim())
    .filter(Boolean);
}

function readStoredCurrentAdminPermissions(): readonly string[] | null {
  if (runtimeCurrentAdminPermissions) return runtimeCurrentAdminPermissions;
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(CURRENT_ADMIN_PERMISSION_STORAGE_KEY);
    if (!raw) return null;
    runtimeCurrentAdminPermissions = normalizePermissionList(JSON.parse(raw));
    return runtimeCurrentAdminPermissions;
  } catch {
    return null;
  }
}

function getResolvedPermissionMap(): Record<AdminStaffRole, readonly string[]> {
  const overrides = readStoredPermissionOverrides();
  if (!overrides) return ADMIN_PERMISSION_MAP;
  return {
    admin: overrides.admin ?? ADMIN_PERMISSION_MAP.admin,
    sub_admin: overrides.sub_admin ?? ADMIN_PERMISSION_MAP.sub_admin,
    moderator: overrides.moderator ?? ADMIN_PERMISSION_MAP.moderator,
    support: overrides.support ?? ADMIN_PERMISSION_MAP.support,
    country_head: overrides.country_head ?? ADMIN_PERMISSION_MAP.country_head,
    country_manager: overrides.country_manager ?? ADMIN_PERMISSION_MAP.country_manager,
  };
}

export function setAdminPermissionOverrides(matrix: Record<string, string[]> | null | undefined): void {
  runtimePermissionOverrides = normalizePermissionOverrideMap(matrix ?? null);
  if (typeof window === "undefined") return;

  if (!runtimePermissionOverrides) {
    window.localStorage.removeItem(ADMIN_PERMISSION_OVERRIDE_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(ADMIN_PERMISSION_OVERRIDE_STORAGE_KEY, JSON.stringify(runtimePermissionOverrides));
}

export function setCurrentAdminPermissions(permissions: readonly string[] | null | undefined): void {
  runtimeCurrentAdminPermissions = normalizePermissionList(permissions ?? null);
  if (typeof window === "undefined") return;

  if (!runtimeCurrentAdminPermissions) {
    window.localStorage.removeItem(CURRENT_ADMIN_PERMISSION_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(CURRENT_ADMIN_PERMISSION_STORAGE_KEY, JSON.stringify(runtimeCurrentAdminPermissions));
}

export function clearAdminPermissionOverrides(): void {
  runtimePermissionOverrides = null;
  runtimeCurrentAdminPermissions = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(ADMIN_PERMISSION_OVERRIDE_STORAGE_KEY);
    window.localStorage.removeItem(CURRENT_ADMIN_PERMISSION_STORAGE_KEY);
  }
}

export function isAdminStaffRole(role: string | null | undefined): role is AdminStaffRole {
  return role === "admin" || role === "sub_admin" || role === "moderator" || role === "support" || role === "country_head" || role === "country_manager";
}

export function getAdminPermissions(role: string | null | undefined): readonly string[] {
  if (!isAdminStaffRole(role)) return [];
  const currentUserPermissions = readStoredCurrentAdminPermissions();
  if (currentUserPermissions && currentUserPermissions.length > 0) {
    return currentUserPermissions;
  }
  return getResolvedPermissionMap()[role];
}

export function hasAdminPermission(role: string | null | undefined, permission: string): boolean {
  return getAdminPermissions(role).includes(permission);
}

function hasRole(role: string | null | undefined, allowedRoles: readonly string[]): boolean {
  return typeof role === "string" && allowedRoles.includes(role);
}

export function canAccessAdminBannerManagement(role: string | null | undefined): boolean {
  return hasRole(role, ["admin", "country_manager"]);
}

export function canAccessAdminEmailManagement(role: string | null | undefined): boolean {
  return hasRole(role, ["admin", "country_manager"]);
}

export function canAccessAdminPaymentManagement(role: string | null | undefined): boolean {
  return hasRole(role, ["admin"]);
}

export function canAccessAdminReturnsManagement(role: string | null | undefined): boolean {
  return hasRole(role, ["admin", "support"]);
}

export function canAccessAdminLogisticsPartnerManagement(role: string | null | undefined): boolean {
  return hasRole(role, ["admin", "sub_admin"]);
}

export function canAccessAdminInvoiceManagement(role: string | null | undefined): boolean {
  return hasAdminPermission(role, "orders.manage");
}

export function canManageAdminInvoices(role: string | null | undefined): boolean {
  return hasRole(role, ["admin", "sub_admin"]);
}

export function canAccessAdminProductVerification(role: string | null | undefined): boolean {
  return hasAdminPermission(role, "products.manage") || hasAdminPermission(role, "moderation.products");
}

export function canAccessAdminFlashSales(role: string | null | undefined): boolean {
  return hasRole(role, ["admin"]);
}