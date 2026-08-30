declare const window: Window & typeof globalThis;

export type AdminStaffRole = "admin" | "sub_admin" | "moderator" | "support" | "country_head" | "country_manager";

export interface StaffPermissionGroup {
  key: string;
  label: string;
  permissions: readonly string[];
}

export interface RbacCatalogResponse {
  features: Record<string, string>;
  namespaces: string[];
  feature_list: string[];
}

const RBAC_CATALOG_URL = "/api/v1/rbac/catalog";

// ── In-memory cache (NOT persisted to localStorage for security) ──

let cachedCatalog: RbacCatalogResponse | null = null;
let catalogFetchPromise: Promise<RbacCatalogResponse | null> | null = null;

export async function fetchRbacCatalog(): Promise<RbacCatalogResponse | null> {
  if (catalogFetchPromise) return catalogFetchPromise;
  catalogFetchPromise = (async () => {
    try {
      const resp = await fetch(RBAC_CATALOG_URL, { credentials: "include" });
      if (!resp.ok) return null;
      const data = (await resp.json()) as RbacCatalogResponse;
      cachedCatalog = data;
      return data;
    } catch {
      return cachedCatalog;
    } finally {
      catalogFetchPromise = null;
    }
  })();
  return catalogFetchPromise;
}

export function getAvailablePermissions(): string[] {
  if (cachedCatalog?.feature_list?.length) return cachedCatalog.feature_list;
  return [];
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

function normalizePermissionList(value: unknown): readonly string[] | null {
  if (!Array.isArray(value)) return null;
  return value
    .map((permission) => String(permission).trim())
    .filter(Boolean);
}

function getResolvedPermissionMap(): Record<AdminStaffRole, readonly string[]> {
  if (!runtimePermissionOverrides) return ADMIN_PERMISSION_MAP;
  return {
    admin: runtimePermissionOverrides.admin ?? ADMIN_PERMISSION_MAP.admin,
    sub_admin: runtimePermissionOverrides.sub_admin ?? ADMIN_PERMISSION_MAP.sub_admin,
    moderator: runtimePermissionOverrides.moderator ?? ADMIN_PERMISSION_MAP.moderator,
    support: runtimePermissionOverrides.support ?? ADMIN_PERMISSION_MAP.support,
    country_head: runtimePermissionOverrides.country_head ?? ADMIN_PERMISSION_MAP.country_head,
    country_manager: runtimePermissionOverrides.country_manager ?? ADMIN_PERMISSION_MAP.country_manager,
  };
}

export function setAdminPermissionOverrides(matrix: Record<string, string[]> | null | undefined): void {
  runtimePermissionOverrides = normalizePermissionOverrideMap(matrix ?? null);
}

export function setCurrentAdminPermissions(permissions: readonly string[] | null | undefined): void {
  runtimeCurrentAdminPermissions = normalizePermissionList(permissions ?? null);
}

export function clearAdminPermissionOverrides(): void {
  runtimePermissionOverrides = null;
  runtimeCurrentAdminPermissions = null;
}

export function isAdminStaffRole(role: string | null | undefined): role is AdminStaffRole {
  return role === "admin" || role === "sub_admin" || role === "moderator" || role === "support" || role === "country_head" || role === "country_manager";
}

export function getAdminPermissions(role: string | null | undefined): readonly string[] {
  if (!isAdminStaffRole(role)) return [];
  if (runtimeCurrentAdminPermissions && runtimeCurrentAdminPermissions.length > 0) {
    return runtimeCurrentAdminPermissions;
  }
  return getResolvedPermissionMap()[role];
}

export function hasAdminPermission(role: string | null | undefined, permission: string): boolean {
  const backendPermissions = getAvailablePermissions();
  if (backendPermissions.length > 0) {
    return backendPermissions.includes(permission);
  }
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