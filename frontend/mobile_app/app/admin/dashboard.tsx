/**
 * Admin Dashboard — React Native
 * Full feature-parity with web_app/src/app/admin/dashboard/page.tsx
 * Tabs: analytics, users, suppliers, orders, products, moderation,
 *       coupons, tickets, flash-sales, audit, staff, compare, insights, banner
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
  StyleSheet,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import {
  apiFetch,
  getAdminHierarchyPermissions,
  normalizeCollectionResponse,
  type HierarchyPermissionsResponse,
} from "@/lib/api";
import { connectUserRealtimeSocket, isAdminAlertRealtimeMessage, isTicketRealtimeMessage } from "@/lib/userRealtime";
import { hasAdminPermission } from "@shared/adminPermissions";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles } from "@/theme";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";
import { createRealtimeRefreshScheduler } from "@shared/realtime";
import { AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

// ── Types ──────────────────────────────────────────────────────────────────────

interface AdminStats {
  users: number;
  suppliers: number;
  products: number;
  orders: number;
  revenue: number;
}

interface AdminUser {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: number;
  created_at: string;
}

interface AdminOrder {
  id: number;
  user_id: number;
  total_amount?: number;
  total?: number;
  status: string;
  created_at: string;
}

interface AdminProduct {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
}

interface PendingSupplier {
  id: number;
  username: string;
  email: string;
  created_at: string;
  verification_note?: string;
}

interface PendingProduct {
  id: number;
  name: string;
  category: string;
  price: number;
  created_at: string;
}

interface AdminCoupon {
  id: number;
  code: string;
  discount_type: string;
  value: number;
  min_order: number;
  uses_count: number;
  expires_at?: string;
  is_active: boolean;
}

interface SupportTicket {
  id: number;
  user_id: number;
  username: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
}

interface FlashSale {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
}

interface AuditLog {
  id: number;
  username?: string;
  user_role?: string;
  action: string;
  resource_type?: string;
  status: string;
  created_at: string;
}

interface SupplierStat {
  id: number;
  username: string;
  email: string;
  product_count: number;
  order_count: number;
  revenue: number;
}

interface TopCustomer {
  user_id: number;
  username: string;
  email: string;
  order_count: number;
  total_spent: number;
}

type Tab =
  | "analytics"
  | "users"
  | "suppliers"
  | "orders"
  | "products"
  | "moderation"
  | "coupons"
  | "tickets"
  | "flash-sales"
  | "audit"
  | "staff"
  | "compare"
  | "insights"
  | "hierarchy"
  | "tools";

const ADMIN_ROLES = ["admin", "sub_admin", "moderator", "support"];

// ── Helper Components ──────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  color,
  bg,
  theme,
}: {
  label: string;
  value: string | number;
  color: string;
  bg: string;
  theme: any;
}) {
  return (
    <View
      style={[
        statCardStyles.card,
        { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
      ]}
    >
      <View style={[statCardStyles.iconBox, { backgroundColor: bg }]}>
        <View style={[statCardStyles.dot, { backgroundColor: color }]} />
      </View>
      <Text style={[statCardStyles.value, { color: theme.colors.text }]}>{value}</Text>
      <Text style={[statCardStyles.label, { color: theme.colors.textMuted }]}>{label}</Text>
    </View>
  );
}
const statCardStyles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: "28%",
    borderRadius: 14,
    borderWidth: 1,
    padding: 10,
    margin: 4,
    alignItems: "center",
    gap: 4,
  },
  iconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  dot: { width: 10, height: 10, borderRadius: 5 },
  value: { fontSize: 18, fontWeight: "800" },
  label: { fontSize: 10, fontWeight: "600" },
});

function Badge({ text, color, bg }: { text: string; color: string; bg: string }) {
  return (
    <View style={{ backgroundColor: bg, borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2, alignSelf: "flex-start" }}>
      <Text style={{ color, fontSize: 10, fontWeight: "700" }}>{text}</Text>
    </View>
  );
}

function StatusBadge({ status, theme }: { status: string; theme: AppTheme }) {
  // Map status strings to theme semantic tokens
  const statusConfig: Record<string, { colorToken: keyof typeof colorTokens; bgToken: keyof typeof bgTokens }> = {
    delivered: { colorToken: "success", bgToken: "successBg" },
    confirmed: { colorToken: "info", bgToken: "infoBg" },
    pending: { colorToken: "warning", bgToken: "warningBg" },
    processing: { colorToken: "info", bgToken: "infoBg" },
    shipped: { colorToken: "info", bgToken: "infoBg" },
    cancelled: { colorToken: "danger", bgToken: "dangerBg" },
    refunded: { colorToken: "textMuted", bgToken: "surface2" },
    open: { colorToken: "info", bgToken: "infoBg" },
    closed: { colorToken: "success", bgToken: "successBg" },
    resolved: { colorToken: "success", bgToken: "successBg" },
    success: { colorToken: "success", bgToken: "successBg" },
    failure: { colorToken: "danger", bgToken: "dangerBg" },
    active: { colorToken: "success", bgToken: "successBg" },
    inactive: { colorToken: "textMuted", bgToken: "surface2" },
  };
  
  // Color tokens from theme
  const colorTokens = {
    success: theme.colors.success,
    danger: theme.colors.danger,
    warning: theme.colors.warning,
    info: theme.colors.info,
    textMuted: theme.colors.textMuted,
  };
  
  const bgTokens = {
    successBg: theme.colors.successBg,
    dangerBg: theme.colors.dangerBg,
    warningBg: theme.colors.warningBg,
    infoBg: theme.colors.infoBg,
    surface2: theme.colors.surface2,
  };
  
  const config = statusConfig[status?.toLowerCase()] ?? { colorToken: "textMuted", bgToken: "surface2" };
  const color = colorTokens[config.colorToken];
  const bg = bgTokens[config.bgToken];
  
  return (
    <View style={{ backgroundColor: bg, borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2, alignSelf: "flex-start" }}>
      <Text style={{ color, fontSize: 10, fontWeight: "700" }}>{status}</Text>
    </View>
  );
}

function RoleLabel({ role, theme }: { role: string; theme: AppTheme }) {
  // Role colors from theme tokens
  const roleColors: Record<string, string> = {
    admin: theme.colors.danger,
    sub_admin: theme.colors.danger,
    moderator: theme.colors.info,
    support: theme.colors.success,
    supplier: theme.colors.success,
    customer: theme.colors.textMuted,
    user: theme.colors.textMuted,
  };
  return (
    <Text style={{ color: roleColors[role] ?? theme.colors.textMuted, fontSize: 10, fontWeight: "700" }}>
      {role?.toUpperCase()}
    </Text>
  );
}

function SectionHeader({ title, theme }: { title: string; theme: AppTheme }) {
  return (
    <Text style={{ color: theme.colors.text, fontSize: 14, fontWeight: "800", marginBottom: 8, marginTop: 4 }}>
      {title}
    </Text>
  );
}

function SearchBar({
  value,
  onChange,
  placeholder,
  theme,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  theme: any;
}) {
  return (
    <TextInput
      value={value}
      onChangeText={onChange}
      placeholder={placeholder}
      placeholderTextColor={theme.colors.textMuted}
      style={{
        backgroundColor: theme.colors.surface2,
        color: theme.colors.text,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: theme.colors.border,
        paddingHorizontal: 12,
        paddingVertical: 8,
        fontSize: 13,
        marginBottom: 8,
      }}
    />
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const role = user?.role ?? null;
  const [
    adminDashboardTitle,
    logoutLabel,
    analyticsLabel,
    usersLabel,
    suppliersLabel,
    ordersLabel,
    productsLabel,
    moderationLabel,
    couponsLabel,
    ticketsLabel,
    flashSalesLabel,
    auditLabel,
    hierarchyLabel,
    staffLabel,
    compareLabel,
    insightsLabel,
    toolsLabel,
    loadingDashboardLabel,
    revenueLabel,
    dailyRevenueLabel,
    noRevenueDataLabel,
    topCategoriesLabel,
    adminToolsLabel,
    managePlatformResourcesLabel,
    bannerManagementLabel,
    bannerManagementDescriptionLabel,
    invoiceManagementLabel,
    invoiceManagementDescriptionLabel,
    logisticsPartnersLabel,
    logisticsPartnersDescriptionLabel,
    productVerificationLabel,
    productVerificationDescriptionLabel,
    customersLabel,
    searchUsersLabel,
    pendingVerificationLabel,
    verificationNoteLabel,
    approveLabel,
    rejectLabel,
    allSuppliersLabel,
    searchSuppliersLabel,
    orderLabel,
    searchOrdersLabel,
    searchProductsLabel,
    stockLabel,
    pendingProductsLabel,
    noProductsPendingReviewLabel,
    rejectionNoteLabel,
    createCouponLabel,
    codeExampleLabel,
    percentLabel,
    fixedLabel,
    discountPercentLabel,
    amountOffLabel,
    usedLabel,
    deleteLabel,
    supportTicketsLabel,
    byLabel,
    priorityLabel,
    noFlashSalesConfiguredLabel,
    auditLogsLabel,
    totalLabel,
    prevLabel,
    nextLabel,
    pageLabel,
    staffAccountsLabel,
    addStaffLabel,
    newStaffAccountLabel,
    usernameLabel,
    emailLabel,
    passwordLabel,
    createAccountLabel,
    searchStaffLabel,
    supplierPerformanceComparisonLabel,
    noDataAvailableLabel,
    roleHierarchyPermissionsLabel,
    couldNotLoadHierarchyPermissionsLabel,
    currentRoleLabel,
    effectivePermissionsLabel,
    topCustomersLabel,
    topPurchasedCategoriesLabel,
    unitsLabel,
    systemLabel,
    activeLabel,
    inactiveLabel,
    cancelLabel,
    deleteCouponTitleLabel,
    deleteCouponPromptLabel,
  ] = useTranslateTexts([
    "Admin Dashboard",
    "Logout",
    "Analytics",
    "Users",
    "Suppliers",
    "Orders",
    "Products",
    "Moderation",
    "Coupons",
    "Tickets",
    "Flash Sales",
    "Audit",
    "Hierarchy",
    "Staff",
    "Compare",
    "Insights",
    "Tools",
    "Loading Dashboard…",
    "Revenue",
    "Daily Revenue — Last 30 Days",
    "No revenue data yet",
    "Top Categories",
    "Admin Tools",
    "Manage platform resources",
    "Banner Management",
    "Manage homepage promotional banners",
    "Invoice Management",
    "Track and manage all platform invoices",
    "Logistics Partners",
    "Register and manage delivery partners",
    "Product Verification",
    "Track product quality checks & inspections",
    "Customers",
    "Search users…",
    "Pending Verification",
    "Verification note (optional)",
    "Approve",
    "Reject",
    "All Suppliers",
    "Search suppliers…",
    "Order",
    "Search orders…",
    "Search products…",
    "Stock",
    "Pending Products",
    "No products pending review",
    "Rejection note (optional)",
    "Create Coupon",
    "Code (e.g. SAVE20)",
    "Percent",
    "Fixed",
    "Discount % (e.g. 15)",
    "Amount off",
    "Used",
    "Delete",
    "Support Tickets",
    "By",
    "priority",
    "No flash sales configured",
    "Audit Logs",
    "Total",
    "Prev",
    "Next",
    "Page",
    "Staff Accounts",
    "Add Staff",
    "New Staff Account",
    "Username",
    "Email",
    "Password",
    "Create Account",
    "Search staff…",
    "Supplier Performance Comparison",
    "No data available",
    "Role Hierarchy & Permissions",
    "Could not load hierarchy permissions.",
    "Current Role",
    "Effective permissions",
    "Top Customers",
    "Top Purchased Categories",
    "units",
    "system",
    "Active",
    "Inactive",
    "Cancel",
    "Delete Coupon",
    "Are you sure?",
  ]);

  const [tab, setTab] = useState<Tab>("analytics");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");

  // Data
  const [stats, setStats] = useState<AdminStats>({ users: 0, suppliers: 0, products: 0, orders: 0, revenue: 0 });
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [dailyData, setDailyData] = useState<{ date: string; revenue: number; orders: number }[]>([]);
  const [topCategories, setTopCategories] = useState<{ category: string; count: number }[]>([]);

  // Supplier verification
  const [pendingSuppliers, setPendingSuppliers] = useState<PendingSupplier[]>([]);
  const [pendingNotes, setPendingNotes] = useState<Record<number, string>>({});
  const [pendingActionId, setPendingActionId] = useState<number | null>(null);

  // Product moderation
  const [pendingProducts, setPendingProducts] = useState<PendingProduct[]>([]);
  const [rejectNotes, setRejectNotes] = useState<Record<number, string>>({});
  const [moderationActionId, setModerationActionId] = useState<number | null>(null);

  // Coupons
  const [coupons, setCoupons] = useState<AdminCoupon[]>([]);
  const [showCouponForm, setShowCouponForm] = useState(false);
  const [couponCode, setCouponCode] = useState("");
  const [couponValue, setCouponValue] = useState("10");
  const [couponType, setCouponType] = useState<"percent" | "fixed">("percent");

  // Tickets
  const [tickets, setTickets] = useState<SupportTicket[]>([]);

  // Flash sales
  const [flashSales, setFlashSales] = useState<FlashSale[]>([]);

  // Audit
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotal, setAuditTotal] = useState(0);

  // Staff
  const [showStaffForm, setShowStaffForm] = useState(false);
  const [staffUsername, setStaffUsername] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [staffPassword, setStaffPassword] = useState("");
  const [staffRole, setStaffRole] = useState("moderator");

  // Compare / insights
  const [supplierStats, setSupplierStats] = useState<SupplierStat[]>([]);
  const [topCustomers, setTopCustomers] = useState<TopCustomer[]>([]);
  const [topCatPurchased, setTopCatPurchased] = useState<{ category: string; units_sold: number }[]>([]);
  const [hierarchyPermissions, setHierarchyPermissions] = useState<HierarchyPermissionsResponse | null>(null);

  const isAdmin = user?.role === "admin";

  // ── Auth guard ──────────────────────────────────────────────────────────────

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (user && !ADMIN_ROLES.includes(user.role)) {
      router.replace("/admin/login" as never);
    }
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Initial data load ──────────────────────────────────────────────────────

  const loadAll = useCallback(async () => {
    try {
      const canReadUsers = hasAdminPermission(role, "users.read");
      const canManageProducts = hasAdminPermission(role, "products.manage");
      const canManageOrders = hasAdminPermission(role, "orders.manage");
      const canViewAnalytics = hasAdminPermission(role, "analytics.view");
      const [usersRes, productsRes, ordersRes, analyticsRes] = await Promise.all([
        canReadUsers ? apiFetch<AdminUser[]>("/admin/users?limit=100").catch(() => []) : Promise.resolve([]),
        canManageProducts ? apiFetch<AdminProduct[]>("/admin/products?limit=100").catch(() => []) : Promise.resolve([]),
        canManageOrders ? apiFetch<AdminOrder[]>("/admin/orders?limit=100").catch(() => []) : Promise.resolve([]),
        canViewAnalytics ? apiFetch<any>("/admin/analytics").catch(() => ({})) : Promise.resolve({}),
      ]);

      const u = Array.isArray(usersRes) ? usersRes : [];
      const p = Array.isArray(productsRes) ? productsRes : [];
      const o = Array.isArray(ordersRes) ? ordersRes : [];
      setUsers(u);
      setProducts(p);
      setOrders(o);

      if (analyticsRes && typeof analyticsRes === "object") {
        setStats({
          users: analyticsRes.total_users ?? u.length,
          suppliers: canReadUsers ? u.filter((x) => x.role === "supplier").length : (analyticsRes.total_suppliers ?? 0),
          products: analyticsRes.total_products ?? p.length,
          orders: analyticsRes.total_orders ?? o.length,
          revenue: analyticsRes.total_revenue ?? 0,
        });
        setDailyData(analyticsRes.daily_data ?? []);
        setTopCategories(analyticsRes.top_categories ?? []);
      }
    } catch {}
    setLoading(false);
    setRefreshing(false);
  }, [role]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadAll(); }, []);

  const loadPendingSuppliers = useCallback(async () => {
    if (!hasAdminPermission(role, "moderation.suppliers")) {
      return;
    }
    try {
      const data = await apiFetch<any>("/admin/suppliers/pending");
      setPendingSuppliers(normalizeCollectionResponse<PendingSupplier>(data));
    } catch {}
  }, [role]);

  const loadPendingProducts = useCallback(async () => {
    if (!hasAdminPermission(role, "moderation.products")) {
      return;
    }
    try {
      const data = await apiFetch<any>("/admin/products/pending");
      setPendingProducts(normalizeCollectionResponse<PendingProduct>(data));
    } catch {}
  }, [role]);

  const loadTickets = useCallback(async () => {
    if (!hasAdminPermission(role, "tickets.manage")) {
      return;
    }
    try {
      const data = await apiFetch<any>("/admin/tickets");
      setTickets(normalizeCollectionResponse<SupportTicket>(data));
    } catch {}
  }, [role]);

  const loadAuditLogs = useCallback(async () => {
    if (!hasAdminPermission(role, "audit.read")) {
      return;
    }
    try {
      const data = await apiFetch<any>(`/admin/audit-logs?page=${auditPage}&page_size=30`);
      setAuditLogs(data?.items ?? []);
      setAuditTotal(data?.total ?? 0);
    } catch {}
  }, [auditPage, role]);

  // ── Tab-specific loaders ───────────────────────────────────────────────────

  useEffect(() => {
    if (tab === "suppliers") {
      void loadPendingSuppliers();
    }
    if (tab === "moderation") {
      void loadPendingProducts();
    }
    if (tab === "coupons") {
      if (hasAdminPermission(role, "coupons.manage")) apiFetch<AdminCoupon[] | { items: AdminCoupon[] }>("/admin/coupons").then((d) =>
        setCoupons(Array.isArray(d) ? d : d?.items ?? [])
      ).catch(() => {});
    }
    if (tab === "tickets") {
      void loadTickets();
    }
    if (tab === "flash-sales") {
      apiFetch<FlashSale[]>("/admin/flash-sales").then((d) =>
        setFlashSales(Array.isArray(d) ? d : [])
      ).catch(() => {});
    }
    if (tab === "audit") {
      void loadAuditLogs();
    }
    if (tab === "compare") {
      if (hasAdminPermission(role, "analytics.view")) apiFetch<any>("/admin/suppliers/comparison").then((d) =>
        setSupplierStats(normalizeCollectionResponse<any>(d))
      ).catch(() => {});
    }
    if (tab === "insights") {
      if (hasAdminPermission(role, "analytics.view")) apiFetch<any>("/admin/customers/insights").then((d) => {
        setTopCustomers(d?.top_customers ?? []);
        setTopCatPurchased(d?.top_categories ?? []);
      }).catch(() => {});
    }
    if (tab === "hierarchy") {
      if (hasAdminPermission(role, "hierarchy.view")) getAdminHierarchyPermissions()
        .then((d) => setHierarchyPermissions(d))
        .catch(() => setHierarchyPermissions(null));
    }
  }, [auditPage, loadAuditLogs, loadPendingProducts, loadPendingSuppliers, loadTickets, role, tab]);

  useEffect(() => {
    if (!user || !ADMIN_ROLES.includes(user.role)) {
      return;
    }

    const supplierScheduler = createRealtimeRefreshScheduler(loadPendingSuppliers);
    const productScheduler = createRealtimeRefreshScheduler(loadPendingProducts);
    const ticketScheduler = createRealtimeRefreshScheduler(loadTickets);
    const auditScheduler = createRealtimeRefreshScheduler(loadAuditLogs);

    const socket = connectUserRealtimeSocket(
      () => undefined,
      (payload) => {
        if (isTicketRealtimeMessage(payload) && hasAdminPermission(role, "tickets.manage")) {
          ticketScheduler.trigger();
        }

        if (!payload || !isAdminAlertRealtimeMessage(payload)) {
          return;
        }

        switch (payload.type) {
          case "admin.alert.audit":
            if (tab === "audit" && hasAdminPermission(role, "audit.read")) {
              auditScheduler.trigger();
            }
            break;
          case "admin.alert.product":
            if (hasAdminPermission(role, "moderation.products")) {
              productScheduler.trigger();
            }
            break;
          case "admin.alert.supplier":
            if (hasAdminPermission(role, "moderation.suppliers")) {
              supplierScheduler.trigger();
            }
            break;
          case "admin.alert.ticket":
            if (hasAdminPermission(role, "tickets.manage")) {
              ticketScheduler.trigger();
            }
            break;
          default:
            break;
        }
      },
    );

    return () => {
      auditScheduler.cancel();
      productScheduler.cancel();
      supplierScheduler.cancel();
      ticketScheduler.cancel();
      socket?.close();
    };
  }, [loadAuditLogs, loadPendingProducts, loadPendingSuppliers, loadTickets, role, tab, user]);

  // ── Actions ────────────────────────────────────────────────────────────────

  const verifySupplier = async (id: number) => {
    setPendingActionId(id);
    const note = pendingNotes[id] || "";
    const qs = note ? `?note=${encodeURIComponent(note)}` : "";
    try {
      await apiFetch(`/admin/suppliers/${id}/verify${qs}`, { method: "POST" });
      setPendingSuppliers((prev) => prev.filter((s) => s.id !== id));
    } catch {}
    setPendingActionId(null);
  };

  const rejectSupplier = async (id: number) => {
    setPendingActionId(id);
    const note = pendingNotes[id] || "";
    const qs = note ? `?note=${encodeURIComponent(note)}` : "";
    try {
      await apiFetch(`/admin/suppliers/${id}/reject${qs}`, { method: "POST" });
      setPendingSuppliers((prev) => prev.filter((s) => s.id !== id));
    } catch {}
    setPendingActionId(null);
  };

  const approveProduct = async (id: number) => {
    setModerationActionId(id);
    try {
      await apiFetch(`/admin/products/${id}/approve`, { method: "POST" });
      setPendingProducts((prev) => prev.filter((p) => p.id !== id));
    } catch {}
    setModerationActionId(null);
  };

  const rejectProduct = async (id: number) => {
    setModerationActionId(id);
    const note = rejectNotes[id] || "";
    const qs = note ? `?note=${encodeURIComponent(note)}` : "";
    try {
      await apiFetch(`/admin/products/${id}/reject${qs}`, { method: "POST" });
      setPendingProducts((prev) => prev.filter((p) => p.id !== id));
    } catch {}
    setModerationActionId(null);
  };

  const deleteCoupon = async (id: number) => {
    Alert.alert(deleteCouponTitleLabel, deleteCouponPromptLabel, [
      { text: cancelLabel, style: "cancel" },
      {
        text: deleteLabel,
        style: "destructive",
        onPress: async () => {
          try {
            await apiFetch(`/admin/coupons/${id}`, { method: "DELETE" });
            setCoupons((prev) => prev.filter((c) => c.id !== id));
          } catch {}
        },
      },
    ]);
  };

  const createCoupon = async () => {
    if (!couponCode.trim()) return;
    try {
      const res = await apiFetch<AdminCoupon>("/admin/coupons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: couponCode,
          discount_type: couponType,
          value: parseFloat(couponValue) || 0,
          min_order: 0,
          is_active: true,
        }),
      });
      if (res && (res as any).id) {
        setCoupons((prev) => [res as AdminCoupon, ...prev]);
        setCouponCode("");
        setCouponValue("10");
        setShowCouponForm(false);
      }
    } catch {}
  };

  const createStaff = async () => {
    if (!staffUsername || !staffEmail || !staffPassword) return;
    try {
      await apiFetch("/admin/staff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: staffUsername, email: staffEmail, password: staffPassword, role: staffRole }),
      });
      setShowStaffForm(false);
      setStaffUsername("");
      setStaffEmail("");
      setStaffPassword("");
      loadAll();
    } catch {}
  };

  const toggleUserActive = async (u: AdminUser) => {
    try {
      await apiFetch(`/admin/users/${u.id}/toggle-active`, { method: "POST" });
      setUsers((prev) =>
        prev.map((x) => (x.id === u.id ? { ...x, is_active: x.is_active ? 0 : 1 } : x))
      );
    } catch {}
  };

  // ── Filtered lists ─────────────────────────────────────────────────────────

  const q = search.toLowerCase();

  const filteredUsers = users.filter(
    (u) =>
      !["admin", "sub_admin", "moderator", "support", "supplier"].includes(u.role) &&
      (!q || u.username?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q))
  );
  const filteredSuppliers = users.filter(
    (u) =>
      u.role === "supplier" &&
      (!q || u.username?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q))
  );
  const filteredStaff = users.filter(
    (u) =>
      ["admin", "sub_admin", "moderator", "support"].includes(u.role) &&
      (!q || u.username?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q))
  );
  const filteredOrders = orders.filter(
    (o) => !q || String(o.id).includes(q) || o.status?.toLowerCase().includes(q)
  );
  const filteredProducts = products.filter(
    (p) => !q || p.name?.toLowerCase().includes(q) || p.category?.toLowerCase().includes(q)
  );

  // ── Tab definitions ────────────────────────────────────────────────────────

  const allTabs: { key: Tab; label: string; adminOnly?: boolean }[] = [
    { key: "analytics", label: analyticsLabel },
    { key: "users", label: usersLabel },
    { key: "suppliers", label: `${suppliersLabel}${pendingSuppliers.length > 0 ? ` (${pendingSuppliers.length})` : ""}` },
    { key: "orders", label: ordersLabel },
    { key: "products", label: productsLabel },
    { key: "moderation", label: `${moderationLabel}${pendingProducts.length > 0 ? ` (${pendingProducts.length})` : ""}` },
    { key: "coupons", label: couponsLabel, adminOnly: true },
    { key: "tickets", label: `${ticketsLabel}${tickets.filter((t) => t.status === "open").length > 0 ? ` (${tickets.filter((t) => t.status === "open").length})` : ""}` },
    { key: "flash-sales", label: flashSalesLabel, adminOnly: true },
    { key: "audit", label: auditLabel },
    { key: "hierarchy", label: hierarchyLabel },
    { key: "staff", label: staffLabel, adminOnly: true },
    { key: "compare", label: compareLabel },
    { key: "insights", label: insightsLabel },
    { key: "tools", label: `🛠 ${toolsLabel}`, adminOnly: true },
  ];

  const TABS = allTabs.filter((t) => !t.adminOnly || isAdmin);

  if (loading) {
    return (
      <View style={[s.container, isRtl ? { direction: "rtl" } : undefined, { justifyContent: "center", alignItems: "center" }]}> 
        <ActivityIndicator size="large" color={theme.colors.brand} />
        <Text style={[s.textMuted, { marginTop: 12 }]}>{loadingDashboardLabel}</Text>
      </View>
    );
  }

  // ── Render helpers ─────────────────────────────────────────────────────────

  const renderUserRow = (u: AdminUser) => (
    <View
      key={u.id}
      style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
    >
      <View style={{ flex: 1 }}>
        <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.sm }]}>{u.username}</Text>
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{u.email}</Text>
        <RoleLabel role={u.role} theme={theme} />
      </View>
      <TouchableOpacity
        onPress={() => toggleUserActive(u)}
        style={[
          styles.actionBtn,
          { backgroundColor: u.is_active ? theme.colors.successBg : theme.colors.dangerBg },
        ]}
      >
        <Text style={{ color: u.is_active ? theme.colors.success : theme.colors.danger, fontSize: 11, fontWeight: "700" }}>
          {u.is_active ? activeLabel : inactiveLabel}
        </Text>
      </TouchableOpacity>
    </View>
  );

  // ── Revenue bar chart ──────────────────────────────────────────────────────

  const maxRevenue = Math.max(...dailyData.map((d) => d.revenue), 1);

  // ── Main render ────────────────────────────────────────────────────────────

  return (
    <View testID="admin-dashboard-screen" style={[s.container, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen
        options={{
          title: adminDashboardTitle,
          headerRight: () => (
            <TouchableOpacity
              onPress={() => { logout(); router.replace("/admin/login" as never); }}
              style={{ marginRight: 12 }}
            >
              <Text style={{ color: theme.colors.danger, fontWeight: "700", fontSize: 13 }}>{logoutLabel}</Text>
            </TouchableOpacity>
          ),
        }}
      />

      {/* ── Tab Bar ───────────────────────────────────────────────────────── */}
      <ScrollView
        testID="admin-dashboard-tab-bar"
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0, borderBottomWidth: 1, borderColor: theme.colors.border }}
        contentContainerStyle={{ paddingHorizontal: 8, paddingVertical: 6, gap: 4 }}
      >
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.key}
            testID={`admin-dashboard-tab-${t.key}`}
            onPress={() => { setTab(t.key); setSearch(""); }}
            style={[
              styles.tabBtn,
              tab === t.key
                ? { backgroundColor: theme.colors.brand }
                : { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, borderWidth: 1 },
            ]}
          >
            <Text
              style={{
                fontSize: 11,
                fontWeight: "700",
                color: tab === t.key ? theme.colors.onBrand : theme.colors.textMuted,
              }}
            >
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* ── Stats Row ─────────────────────────────────────────────────────── */}
      {tab === "analytics" && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ flexGrow: 0 }}
          contentContainerStyle={{ padding: 8, gap: 4 }}
        >
          <StatCard label={usersLabel} value={stats.users} color={theme.colors.info} bg={theme.colors.infoBg} theme={theme} />
          <StatCard label={suppliersLabel} value={stats.suppliers} color={theme.colors.success} bg={theme.colors.successBg} theme={theme} />
          <StatCard label={productsLabel} value={stats.products} color={theme.colors.success} bg={theme.colors.successBg} theme={theme} />
          <StatCard label={ordersLabel} value={stats.orders} color={theme.colors.warning} bg={theme.colors.warningBg} theme={theme} />
          <StatCard label={revenueLabel} value={formatMoney(stats.revenue)} color={theme.colors.danger} bg={theme.colors.dangerBg} theme={theme} />
        </ScrollView>
      )}

      {/* ── Main Content ──────────────────────────────────────────────────── */}
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 12, paddingBottom: 40 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadAll(); }} tintColor={theme.colors.brand} />
        }
      >
        {/* ═══════════════ ANALYTICS ═══════════════ */}
        {tab === "analytics" && (
          <View testID="admin-dashboard-analytics-panel" style={{ gap: 12 }}>
            {/* Revenue chart */}
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <SectionHeader title={dailyRevenueLabel} theme={theme} />
              {dailyData.length === 0 ? (
                <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 16 }]}>{noRevenueDataLabel}</Text>
              ) : (
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={{ flexDirection: "row", alignItems: "flex-end", height: 80, gap: 2 }}>
                    {dailyData.map((d, i) => (
                      <View key={i} style={{ alignItems: "center", gap: 2, width: 10 }}>
                        <View
                          style={{
                            width: 8,
                            backgroundColor: theme.colors.brand,
                            borderRadius: 2,
                            height: Math.max(4, (d.revenue / maxRevenue) * 70),
                          }}
                        />
                      </View>
                    ))}
                  </View>
                </ScrollView>
              )}
            </View>

            {/* Top categories */}
            {topCategories.length > 0 && (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <SectionHeader title={topCategoriesLabel} theme={theme} />
                {topCategories.slice(0, 5).map((c, i) => {
                  const maxCount = Math.max(...topCategories.map((x) => x.count), 1);
                  return (
                    <View key={i} style={{ marginBottom: 6 }}>
                      <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 3 }}>
                        <Text style={[s.textMuted, { fontSize: 12 }]}>{c.category}</Text>
                        <Text style={[s.text, { fontSize: 12, fontWeight: "700" }]}>{c.count}</Text>
                      </View>
                      <View style={{ height: 4, borderRadius: 2, backgroundColor: theme.colors.surface2, overflow: "hidden" }}>
                        <View
                          style={{ height: 4, borderRadius: 2, backgroundColor: theme.colors.brand, width: `${(c.count / maxCount) * 100}%` }}
                        />
                      </View>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        )}

        {/* ═══════════════ USERS ═══════════════ */}
        {tab === "users" && (
          <View testID="admin-dashboard-users-panel">
            <SectionHeader title={`${customersLabel} (${filteredUsers.length})`} theme={theme} />
            <SearchBar value={search} onChange={setSearch} placeholder={searchUsersLabel} theme={theme} />
            {filteredUsers.map(renderUserRow)}
          </View>
        )}

        {/* ═══════════════ SUPPLIERS ═══════════════ */}
        {tab === "suppliers" && (
          <View testID="admin-dashboard-suppliers-panel" style={{ gap: 12 }}>
            {pendingSuppliers.length > 0 && (
              <View>
                <SectionHeader title={`${pendingVerificationLabel} (${pendingSuppliers.length})`} theme={theme} />
                {pendingSuppliers.map((ps) => (
                  <View key={ps.id} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.warning }]}>
                    <Text style={[s.text, { fontWeight: "700" }]}>{ps.username}</Text>
                    <Text style={[s.textMuted, { fontSize: 12 }]}>{ps.email}</Text>
                    <TextInput
                      placeholder={verificationNoteLabel}
                      placeholderTextColor={theme.colors.textMuted}
                      value={pendingNotes[ps.id] ?? ""}
                      onChangeText={(v) => setPendingNotes((prev) => ({ ...prev, [ps.id]: v }))}
                      style={[s.input, { marginTop: 6, fontSize: 12 }]}
                    />
                    <View style={{ flexDirection: "row", gap: 8, marginTop: 8 }}>
                      <TouchableOpacity
                        onPress={() => verifySupplier(ps.id)}
                        disabled={pendingActionId === ps.id}
                        style={[styles.actionBtn, { backgroundColor: theme.colors.successBg, flex: 1 }]}
                      >
                        <Text style={{ color: theme.colors.success, fontWeight: "700", textAlign: "center" }}>
                          {pendingActionId === ps.id ? "…" : `✓ ${approveLabel}`}
                        </Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={() => rejectSupplier(ps.id)}
                        disabled={pendingActionId === ps.id}
                        style={[styles.actionBtn, { backgroundColor: theme.colors.dangerBg, flex: 1 }]}
                      >
                        <Text style={{ color: theme.colors.danger, fontWeight: "700", textAlign: "center" }}>
                          ✗ {rejectLabel}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}
              </View>
            )}
            <SectionHeader title={allSuppliersLabel} theme={theme} />
            <SearchBar value={search} onChange={setSearch} placeholder={searchSuppliersLabel} theme={theme} />
            {filteredSuppliers.map(renderUserRow)}
          </View>
        )}

        {/* ═══════════════ ORDERS ═══════════════ */}
        {tab === "orders" && (
          <View testID="admin-dashboard-orders-panel">
            <SectionHeader title={`Orders (${filteredOrders.length})`} theme={theme} />
            <SearchBar value={search} onChange={setSearch} placeholder={searchOrdersLabel} theme={theme} />
            {filteredOrders.map((o) => (
              <View key={o.id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{orderLabel} #{o.id}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{formatLocalizedDate(o.created_at, locale, { year: "numeric", month: "short", day: "numeric" })}</Text>
                  <StatusBadge status={o.status} theme={theme} />
                </View>
                <Text style={[s.text, { fontWeight: "800", color: theme.colors.brand }]}>
                  {formatMoney((o.total_amount || o.total) ?? 0)}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* ═══════════════ PRODUCTS ═══════════════ */}
        {tab === "products" && (
          <View testID="admin-dashboard-products-panel">
            <SectionHeader title={`Products (${filteredProducts.length})`} theme={theme} />
            <SearchBar value={search} onChange={setSearch} placeholder={searchProductsLabel} theme={theme} />
            {filteredProducts.map((p) => (
              <View key={p.id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]} numberOfLines={1}>{p.name}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{p.category}</Text>
                </View>
                <View style={{ alignItems: "flex-end", gap: 4 }}>
                  <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{formatMoney(p.price)}</Text>
                  <Text style={{ color: p.stock <= 5 ? theme.colors.warning : theme.colors.success, fontSize: 11 }}>
                    {stockLabel}: {p.stock}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* ═══════════════ MODERATION ═══════════════ */}
        {tab === "moderation" && (
          <View testID="admin-dashboard-moderation-panel">
            <SectionHeader title={`${pendingProductsLabel} (${pendingProducts.length})`} theme={theme} />
            {pendingProducts.length === 0 ? (
              <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>{noProductsPendingReviewLabel}</Text>
            ) : (
              pendingProducts.map((p) => (
                <View key={p.id} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{p.name}</Text>
                  <Text style={[s.textMuted, { fontSize: 12 }]}>{p.category} · {formatMoney(p.price)}</Text>
                  <TextInput
                    placeholder={rejectionNoteLabel}
                    placeholderTextColor={theme.colors.textMuted}
                    value={rejectNotes[p.id] ?? ""}
                    onChangeText={(v) => setRejectNotes((prev) => ({ ...prev, [p.id]: v }))}
                    style={[s.input, { marginTop: 6, fontSize: 12 }]}
                  />
                  <View style={{ flexDirection: "row", gap: 8, marginTop: 8 }}>
                    <TouchableOpacity
                      onPress={() => approveProduct(p.id)}
                      disabled={moderationActionId === p.id}
style={[styles.actionBtn, { backgroundColor: theme.colors.successBg, flex: 1 }]}
                      >
                      <Text style={{ color: theme.colors.success, fontWeight: "700", textAlign: "center" }}>
                          {moderationActionId === p.id ? "…" : `✓ ${approveLabel}`}
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={() => rejectProduct(p.id)}
                      disabled={moderationActionId === p.id}
                      style={[styles.actionBtn, { backgroundColor: theme.colors.dangerBg, flex: 1 }]}
                    >
                        <Text style={{ color: theme.colors.danger, fontWeight: "700", textAlign: "center" }}>✗ {rejectLabel}</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* ═══════════════ COUPONS ═══════════════ */}
        {tab === "coupons" && (
          <View testID="admin-dashboard-coupons-panel">
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <SectionHeader title={`Coupons (${coupons.length})`} theme={theme} />
              <TouchableOpacity
                onPress={() => setShowCouponForm(!showCouponForm)}
                style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}
              >
                <Text style={{ color: "#fff", fontWeight: "700", fontSize: 12 }}>+ {createCouponLabel}</Text>
              </TouchableOpacity>
            </View>

            {showCouponForm && (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginBottom: 12 }]}>
                <Text style={[s.text, { fontWeight: "700", marginBottom: 8 }]}>{createCouponLabel}</Text>
                <TextInput
                  placeholder={codeExampleLabel}
                  placeholderTextColor={theme.colors.textMuted}
                  value={couponCode}
                  onChangeText={setCouponCode}
                  autoCapitalize="characters"
                  style={[s.input, { marginBottom: 6 }]}
                />
                <View style={{ flexDirection: "row", gap: 6, marginBottom: 6 }}>
                  {(["percent", "fixed"] as const).map((t) => (
                    <TouchableOpacity
                      key={t}
                      onPress={() => setCouponType(t)}
                      style={[
                        styles.actionBtn,
                        { flex: 1, backgroundColor: couponType === t ? theme.colors.brand : theme.colors.surface2 },
                      ]}
                    >
                      <Text style={{ color: couponType === t ? "#fff" : theme.colors.textMuted, textAlign: "center", fontWeight: "600", fontSize: 12 }}>
                        {t === "percent" ? `% ${percentLabel}` : `${fixedLabel}`}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
                <TextInput
                  placeholder={couponType === "percent" ? discountPercentLabel : amountOffLabel}
                  placeholderTextColor={theme.colors.textMuted}
                  value={couponValue}
                  onChangeText={setCouponValue}
                  keyboardType="numeric"
                  style={[s.input, { marginBottom: 8 }]}
                />
                <TouchableOpacity onPress={createCoupon} style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}>
                  <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center" }}>{createCouponLabel}</Text>
                </TouchableOpacity>
              </View>
            )}

            {coupons.map((c) => (
              <View key={c.id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "800", letterSpacing: 1 }]}>{c.code}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>
                    {c.discount_type === "percent" ? `${c.value}% ${fixedLabel === "Fixed" ? "off" : "off"}` : `${formatMoney(c.value)} off`}
                    {c.min_order > 0 ? ` · min ${formatMoney(c.min_order)}` : ""}
                  </Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{usedLabel}: {c.uses_count}×</Text>
                </View>
                <View style={{ gap: 6, alignItems: "flex-end" }}>
                  <StatusBadge status={c.is_active ? "active" : "inactive"} theme={theme} />
                  <TouchableOpacity onPress={() => deleteCoupon(c.id)}>
                    <Text style={{ color: theme.colors.danger, fontSize: 11, fontWeight: "700" }}>{deleteLabel}</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* ═══════════════ TICKETS ═══════════════ */}
        {tab === "tickets" && (
          <View testID="admin-dashboard-tickets-panel">
            <SectionHeader title={`${supportTicketsLabel} (${tickets.length})`} theme={theme} />
            {tickets.map((t) => (
              <View key={t.id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]} numberOfLines={1}>{t.subject}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{byLabel} {t.username} · {t.priority} {priorityLabel}</Text>
                  <StatusBadge status={t.status} theme={theme} />
                </View>
                <Text style={[s.textMuted, { fontSize: 11 }]}>{formatLocalizedDate(t.created_at, locale, { year: "numeric", month: "short", day: "numeric" })}</Text>
              </View>
            ))}
          </View>
        )}

        {/* ═══════════════ FLASH SALES ═══════════════ */}
        {tab === "flash-sales" && (
          <View testID="admin-dashboard-flash-sales-panel">
            <SectionHeader title={`Flash Sales (${flashSales.length})`} theme={theme} />
            {flashSales.length === 0 ? (
              <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>{noFlashSalesConfiguredLabel}</Text>
            ) : (
              flashSales.map((f) => (
                <View key={f.id} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                    <Text style={[s.text, { fontWeight: "700" }]}>{f.title}</Text>
                    <StatusBadge status={f.is_active ? "active" : "inactive"} theme={theme} />
                  </View>
                  <Text style={[s.textMuted, { fontSize: 12, marginTop: 4 }]}>
                    {f.discount_pct}% off · {formatLocalizedDate(f.starts_at, locale, { year: "numeric", month: "short", day: "numeric" })} → {formatLocalizedDate(f.ends_at, locale, { year: "numeric", month: "short", day: "numeric" })}
                  </Text>
                </View>
              ))
            )}
          </View>
        )}

        {/* ═══════════════ AUDIT ═══════════════ */}
        {tab === "audit" && (
          <View testID="admin-dashboard-audit-panel">
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <SectionHeader title={auditLogsLabel} theme={theme} />
              <Text style={[s.textMuted, { fontSize: 11 }]}>{totalLabel}: {auditTotal}</Text>
            </View>
            {auditLogs.map((l) => (
              <View key={l.id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700", fontSize: 12 }]}>{l.action}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>
                    {l.username ?? systemLabel} · {l.user_role}
                    {l.resource_type ? ` · ${l.resource_type}` : ""}
                  </Text>
                  <Text style={[s.textMuted, { fontSize: 10 }]}>{formatLocalizedDate(l.created_at, locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text>
                </View>
                <StatusBadge status={l.status} theme={theme} />
              </View>
            ))}
            {/* Pagination */}
            <View style={{ flexDirection: "row", justifyContent: "center", gap: 8, marginTop: 12 }}>
              <TouchableOpacity
                disabled={auditPage <= 1}
                onPress={() => setAuditPage((p) => Math.max(1, p - 1))}
                style={[styles.actionBtn, { backgroundColor: auditPage <= 1 ? theme.colors.surface2 : theme.colors.brand }]}
              >
                <Text style={{ color: auditPage <= 1 ? theme.colors.textMuted : "#fff", fontWeight: "700" }}>{isRtl ? `→ ${prevLabel}` : `← ${prevLabel}`}</Text>
              </TouchableOpacity>
              <Text style={[s.textMuted, { alignSelf: "center" }]}>{pageLabel} {auditPage}</Text>
              <TouchableOpacity
                onPress={() => setAuditPage((p) => p + 1)}
                style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}
              >
                <Text style={{ color: "#fff", fontWeight: "700" }}>{isRtl ? `${nextLabel} ←` : `${nextLabel} →`}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ═══════════════ STAFF ═══════════════ */}
        {tab === "staff" && (
          <View>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <SectionHeader title={`${staffAccountsLabel} (${filteredStaff.length})`} theme={theme} />
              <TouchableOpacity
                onPress={() => setShowStaffForm(!showStaffForm)}
                style={[styles.actionBtn, { backgroundColor: theme.colors.staffGold }]}
              >
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: 12 }}>+ {addStaffLabel}</Text>
              </TouchableOpacity>
            </View>

            {showStaffForm && (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.staffGold, marginBottom: 12 }]}>
                <Text style={[s.text, { fontWeight: "700", marginBottom: 8 }]}>{newStaffAccountLabel}</Text>
                <TextInput placeholder={usernameLabel} placeholderTextColor={theme.colors.textMuted} value={staffUsername} onChangeText={setStaffUsername} style={[s.input, { marginBottom: 6 }]} />
                <TextInput placeholder={emailLabel} placeholderTextColor={theme.colors.textMuted} value={staffEmail} onChangeText={setStaffEmail} keyboardType="email-address" style={[s.input, { marginBottom: 6 }]} />
                <TextInput placeholder={passwordLabel} placeholderTextColor={theme.colors.textMuted} value={staffPassword} onChangeText={setStaffPassword} secureTextEntry style={[s.input, { marginBottom: 6 }]} />
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
                  {["moderator", "support", "sub_admin"].map((r) => (
                    <TouchableOpacity
                      key={r}
                      onPress={() => setStaffRole(r)}
                      style={[styles.actionBtn, { backgroundColor: staffRole === r ? theme.colors.brand : theme.colors.surface2 }]}
                    >
                      <Text style={{ color: staffRole === r ? "#fff" : theme.colors.textMuted, fontSize: 12, fontWeight: "600" }}>{r}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
                <TouchableOpacity onPress={createStaff} style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}>
                  <Text style={{ color: "#fff", fontWeight: "700", textAlign: "center" }}>{createAccountLabel}</Text>
                </TouchableOpacity>
              </View>
            )}

            <SearchBar value={search} onChange={setSearch} placeholder={searchStaffLabel} theme={theme} />
            {filteredStaff.map(renderUserRow)}
          </View>
        )}

        {/* ═══════════════ SUPPLIER COMPARE ═══════════════ */}
        {tab === "compare" && (
          <View>
            <SectionHeader title={supplierPerformanceComparisonLabel} theme={theme} />
            {supplierStats.length === 0 ? (
              <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>{noDataAvailableLabel}</Text>
            ) : (
              supplierStats.map((ss) => (
                <View key={ss.id} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{ss.username}</Text>
                  <Text style={[s.textMuted, { fontSize: 11 }]}>{ss.email}</Text>
                  <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 6 }}>
                    <Badge text={`${ss.product_count} ${productsLabel.toLowerCase()}`} color={theme.colors.info} bg={theme.colors.infoBg} />
                    <Badge text={`${ss.order_count} ${ordersLabel.toLowerCase()}`} color={theme.colors.warning} bg={theme.colors.warningBg} />
                    <Badge text={formatMoney(ss.revenue)} color={theme.colors.success} bg={theme.colors.successBg} />
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* ═══════════════ INSIGHTS ═══════════════ */}
        {tab === "hierarchy" && (
          <View style={{ gap: 12 }}>
            <SectionHeader title={roleHierarchyPermissionsLabel} theme={theme} />
            {!hierarchyPermissions ? (
              <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>
                {couldNotLoadHierarchyPermissionsLabel}
              </Text>
            ) : (
              <>
                <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <Text style={[s.text, { fontWeight: "700", fontSize: 13, marginBottom: 6 }]}>
                    {currentRoleLabel}: {hierarchyPermissions.role}
                  </Text>
                  <Text style={[s.textMuted, { fontSize: 12, marginBottom: 8 }]}>
                    {effectivePermissionsLabel} ({hierarchyPermissions.permissions.length})
                  </Text>
                  <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                    {hierarchyPermissions.permissions.map((permission) => (
                      <View
                        key={permission}
                        style={{
                          borderRadius: 999,
                          borderWidth: 1,
                          borderColor: theme.colors.border,
                          backgroundColor: theme.colors.surface2,
                          paddingHorizontal: 8,
                          paddingVertical: 4,
                        }}
                      >
                        <Text style={[s.textMuted, { fontSize: 10, fontWeight: "700" }]}>{permission}</Text>
                      </View>
                    ))}
                  </View>
                </View>

                {Object.entries(hierarchyPermissions.matrix).map(([role, permissions]) => (
                  <View
                    key={role}
                    style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
                  >
                    <Text style={[s.text, { fontWeight: "700", fontSize: 13, marginBottom: 6 }]}>
                      {role}
                    </Text>
                    <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                      {permissions.map((permission) => (
                        <View
                          key={`${role}-${permission}`}
                          style={{
                            borderRadius: 999,
                            borderWidth: 1,
                            borderColor: theme.colors.border,
                            backgroundColor: theme.colors.surface2,
                            paddingHorizontal: 8,
                            paddingVertical: 4,
                          }}
                        >
                          <Text style={[s.textMuted, { fontSize: 10, fontWeight: "700" }]}>{permission}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                ))}
              </>
            )}
          </View>
        )}

        {tab === "insights" && (
          <View style={{ gap: 12 }}>
            {topCustomers.length > 0 && (
              <View>
                <SectionHeader title={topCustomersLabel} theme={theme} />
                {topCustomers.slice(0, 10).map((tc) => (
                  <View key={tc.user_id} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <View style={{ flex: 1 }}>
                      <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]}>{tc.username}</Text>
                      <Text style={[s.textMuted, { fontSize: 11 }]}>{tc.order_count} {ordersLabel.toLowerCase()}</Text>
                    </View>
                    <Text style={{ color: theme.colors.brand, fontWeight: "800" }}>
                      {formatMoney(tc.total_spent)}
                    </Text>
                  </View>
                ))}
              </View>
            )}
            {topCatPurchased.length > 0 && (
              <View>
                <SectionHeader title={topPurchasedCategoriesLabel} theme={theme} />
                {topCatPurchased.map((c, i) => (
                  <View key={i} style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <Text style={[s.text, { fontWeight: "600", flex: 1 }]}>{c.category}</Text>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{c.units_sold} {unitsLabel}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        )}
        {/* ═══════════════ TOOLS ═══════════════ */}
        {tab === "tools" && (
          <View style={{ gap: 12 }}>
            <SectionHeader title={adminToolsLabel} theme={theme} />
            <Text style={[s.textMuted, { fontSize: 12, marginBottom: 4 }]}>{managePlatformResourcesLabel}</Text>
            {[
              { icon: "images-outline", label: bannerManagementLabel, desc: `${bannerManagementDescriptionLabel} (Promotions hub)`, route: "/admin/promotions?section=banners" },
              { icon: "document-text-outline", label: invoiceManagementLabel, desc: invoiceManagementDescriptionLabel, route: "/admin/invoices" },
              { icon: "car-outline", label: logisticsPartnersLabel, desc: logisticsPartnersDescriptionLabel, route: "/admin/logistics-partners" },
              { icon: "search-outline", label: productVerificationLabel, desc: productVerificationDescriptionLabel, route: "/admin/product-verification" },
              { icon: "mail-outline", label: emailLabel, desc: "Campaigns, templates and newsletter sends", route: "/admin/email" },
              { icon: "cube-outline", label: "Exports", desc: "Queue CSV exports and share them when ready", route: "/admin/exports" },
              { icon: "card-outline", label: "Bank Accounts", desc: "Verify supplier & partner bank accounts", route: "/admin/bank-accounts" },
            ].map(({ icon, label, desc, route }) => (
              <TouchableOpacity
                key={route}
                onPress={() => router.push(route as never)}
                style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
              >
                <Ionicons name={icon as any} size={20} color={theme.colors.brand} style={{ marginRight: 10 }} />
                <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700", fontSize: 14 }]}>{label}</Text>
                  <Text style={[s.textMuted, { fontSize: 12 }]}>{desc}</Text>
                </View>
                <Text style={{ color: theme.colors.brand, fontSize: 20 }}>{isRtl ? "‹" : "›"}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

export function ErrorBoundary({
  error,
  retry,
}: {
  error: Error;
  retry: () => void;
}) {
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 10 }}>
      <Text style={{ fontSize: 16, fontWeight: "700", textAlign: "center" }}>Admin Dashboard Error</Text>
      <Text style={{ fontSize: 12, color: "#6b7280", textAlign: "center" }}>{error.message}</Text>
      <TouchableOpacity
        onPress={retry}
        style={{ backgroundColor: "#32CD32", borderRadius: 10, paddingHorizontal: 16, paddingVertical: 10 }}
      >
        <Text style={{ color: "#fff", fontWeight: "700" }}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  tabBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 12,
    marginBottom: 8,
  },
  row: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    marginBottom: 6,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  actionBtn: {
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
});
