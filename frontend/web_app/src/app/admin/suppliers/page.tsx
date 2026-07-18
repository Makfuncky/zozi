"use client";

import { Button } from "@/components/ui/Button";

import { AnimatePresence, motion } from "framer-motion";
import React, { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Activity,
  AlertCircle,
  ArrowDownUp,
  BadgeCheck,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Download,
  FileCheck2,
  FileUp,
  Loader2,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  Store,
  Upload,
  X,
  XCircle,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import ApprovalActionModal from "@/components/ApprovalActionModal";
import BulkActionBar from "@/components/BulkActionBar";
import { apiFetch } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";
import { normalizeListPage } from "@/lib/listResponse";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useToastStore } from "@/lib/toastStore";
import { hasAdminPermission } from "@shared/adminPermissions";
import { useApprovalCheck } from "@/hooks/useApprovalCheck";
import { dc, useDensity } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

type SupplierSection = "management" | "documents" | "comparison" | "badges" | "activity";

interface SupplierProfileSummary {
  business_name?: string | null;
  business_type?: string | null;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  website?: string | null;
  phone_business?: string | null;
  tax_id?: string | null;
  verification_status?: string | null;
  badge_level?: string | null;
  credibility_score?: number | null;
  verified_at?: string | null;
}

interface SupplierRecord {
  id: number;
  username: string;
  email: string;
  phone?: string | null;
  is_active: boolean | number;
  is_deleted?: boolean;
  is_verified: boolean;
  verification_note?: string | null;
  created_at?: string | null;
  product_count: number;
  order_count: number;
  revenue: number;
  avg_price: number;
  top_product_name?: string | null;
  profile?: SupplierProfileSummary | null;
}

interface SupplierListResponse {
  items: SupplierRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary?: {
    pending_suppliers: number;
    active_suppliers: number;
    suspended_suppliers: number;
    total_revenue: number;
  };
}

interface SupplierDocumentRecord {
  id: number;
  supplier_id: number;
  supplier_username?: string | null;
  document_type: string;
  document_name: string;
  file_url: string;
  status: string;
  review_note?: string | null;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  created_at?: string | null;
}

interface SupplierComparisonRecord {
  id: number;
  username: string;
  email: string;
  product_count: number;
  order_count: number;
  revenue: number;
  avg_price: number;
  growth_rate?: number;
  revenue_share?: number;
  joined?: string | null;
}

interface AuditLogRecord {
  id: number;
  username?: string | null;
  user_role?: string | null;
  action: string;
  details?: string | null;
  status: string;
  created_at: string;
}

interface CreateSupplierFormState {
  username: string;
  email: string;
  password: string;
  business_name: string;
  business_type: string;
  country: string;
  phone: string;
}

interface SupplierCommissionOverrideRow {
  id: number;
  rate: number;
  note: string | null;
  is_active: boolean;
  effective_from: string;
  effective_to: string | null;
}

interface SupplierCommissionState {
  supplier_id: number;
  supplier_name: string;
  current_rate: number;
  calculation_method: string;
  badge_level: string | null;
  default_base_rate?: number;
  combined_default_rate?: number;
  history: SupplierCommissionOverrideRow[];
}

interface BulkDeleteSkipDetail {
  id: number;
  reason: string;
}

interface BulkDeleteUsersResponse {
  deleted?: number;
  skipped?: number;
  skipped_details?: BulkDeleteSkipDetail[];
}

const SECTION_OPTIONS: Array<{ key: SupplierSection; label: string; icon: typeof Store }> = [
  { key: "management", label: "Supplier List", icon: Store },
  { key: "documents", label: "KYC Documents", icon: FileCheck2 },
  { key: "comparison", label: "Comparison", icon: BarChart3 },
  { key: "badges", label: "Credibility & Badges", icon: BadgeCheck },
  { key: "activity", label: "Activity Log", icon: Activity },
];

const STATUS_OPTIONS = ["all", "pending", "approved", "rejected", "suspended"] as const;
const BADGE_FILTER_OPTIONS = ["all", "none", "bronze", "silver", "gold", "verified"] as const;
const BADGE_ASSIGN_OPTIONS = ["none", "bronze", "silver", "gold", "verified"] as const;
const DOCUMENT_STATUS_OPTIONS = ["all", "pending", "under_review", "approved", "rejected", "expired"] as const;

function formatBulkDeleteSkipSummary(skippedDetails?: BulkDeleteSkipDetail[]): string {
  if (!skippedDetails?.length) return "";
  const visibleReasons = skippedDetails
    .slice(0, 2)
    .map((entry) => `#${entry.id}: ${entry.reason}`)
    .join(" | ");
  if (skippedDetails.length <= 2) return visibleReasons;
  return `${visibleReasons} | +${skippedDetails.length - 2} more`;
}

const STATUS_TONE: Record<string, string> = {
  approved: "theme-chip-success",
  pending: "theme-chip-warning",
  rejected: "theme-chip-danger",
  suspended: "theme-chip-danger",
  archived: "theme-chip-danger",
  deleted: "theme-chip-danger",
};

const BADGE_TONE: Record<string, string> = {
  none: "theme-chip-muted",
  bronze: "theme-chip-warning",
  silver: "theme-chip-muted",
  gold: "theme-chip-warning",
  verified: "theme-chip-success",
};

function buildQueryString(params: Record<string, string | number | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "" || value === "all") return;
    searchParams.set(key, String(value));
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function statusForSupplier(supplier: SupplierRecord): string {
  if (supplier.is_deleted) return "deleted";
  const verificationStatus = supplier.profile?.verification_status || "pending";
  if (!Boolean(supplier.is_active) && verificationStatus === "archived") return "archived";
  if (!Boolean(supplier.is_active)) return "suspended";
  if (verificationStatus === "verified" || verificationStatus === "approved") return "approved";
  if (supplier.is_verified && verificationStatus === "pending") return "approved";
  return verificationStatus;
}

function safeDate(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleDateString();
}

function safeDateTime(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

function parseDetails(details?: string | null): string {
  if (!details) return "-";
  try {
    const parsed = JSON.parse(details) as Record<string, unknown>;
    return Object.entries(parsed)
      .slice(0, 4)
      .map(([key, value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`)
      .join(" | ") || "-";
  } catch {
    return details;
  }
}

function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let currentCell = "";
  let currentRow: string[] = [];
  let insideQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    const nextCharacter = text[index + 1];
    if (character === '"') {
      if (insideQuotes && nextCharacter === '"') {
        currentCell += '"';
        index += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
      continue;
    }
    if (character === "," && !insideQuotes) {
      currentRow.push(currentCell.trim());
      currentCell = "";
      continue;
    }
    if ((character === "\n" || character === "\r") && !insideQuotes) {
      if (character === "\r" && nextCharacter === "\n") index += 1;
      currentRow.push(currentCell.trim());
      currentCell = "";
      if (currentRow.some((cell) => cell.length > 0)) rows.push(currentRow);
      currentRow = [];
      continue;
    }
    currentCell += character;
  }

  if (currentCell.length > 0 || currentRow.length > 0) {
    currentRow.push(currentCell.trim());
    if (currentRow.some((cell) => cell.length > 0)) rows.push(currentRow);
  }

  return rows;
}

function generateTemporaryPassword(seed: string) {
  const normalized = seed.replace(/[^a-zA-Z0-9]/g, "").slice(0, 6) || "Zozi";
  return `${normalized}#2026Aa!`;
}

function downloadCsvFile(filename: string, rows: Array<Record<string, unknown>>) {
  if (!rows.length) return;
  const columns = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set<string>()),
  );
  const csv = [
    columns.join(","),
    ...rows.map((row) =>
      columns
        .map((column) => {
          const value = row[column] == null ? "" : String(row[column]);
          return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
        })
        .join(","),
    ),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function StatCard({ icon: Icon, label, value, hint }: { icon: typeof Store; label: string; value: string; hint: string }) {
  return (
    <div className="theme-card rounded-xl border p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-text-faint">{label}</p>
          <p className="mt-1 text-lg font-semibold text-text">{value}</p>
          <p className="mt-0.5 text-[10px] text-text-muted">{hint}</p>
        </div>
        <div className="theme-chip-muted flex h-7 w-7 items-center justify-center rounded-lg">
          <Icon className="h-3.5 w-3.5 text-text-muted" />
        </div>
      </div>
    </div>
  );
}

function AdminSuppliersInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sectionParam = searchParams?.get("section");
  const currentSection: SupplierSection = sectionParam === "compare" ? "comparison" : ((sectionParam as SupplierSection) || "management");
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const addToast = useToastStore((state) => state.addToast);
  const formatMoney = useCurrencyStore((state) => state.format);
  const { canApprove } = useApprovalCheck(user);
  const { selectedCountry } = useAdminCountry();
  const adminCountryCode = selectedCountry?.code && selectedCountry.code !== "*" ? selectedCountry.code : undefined;

  const [suppliers, setSuppliers] = useState<SupplierRecord[]>([]);
  const [summary, setSummary] = useState({ pending_suppliers: 0, active_suppliers: 0, suspended_suppliers: 0, total_revenue: 0 });
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [statusFilter, setStatusFilter] = useState<(typeof STATUS_OPTIONS)[number]>("all");
  const [badgeFilter, setBadgeFilter] = useState<(typeof BADGE_FILTER_OPTIONS)[number]>("all");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [totalSuppliers, setTotalSuppliers] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSupplierIds, setSelectedSupplierIds] = useState<Set<number>>(new Set());
  const [expandedSupplierId, setExpandedSupplierId] = useState<number | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkNote, setBulkNote] = useState("");
  const [bulkBadgeLevel, setBulkBadgeLevel] = useState<(typeof BADGE_ASSIGN_OPTIONS)[number]>("verified");
  const [rowBadgeDrafts, setRowBadgeDrafts] = useState<Record<number, string>>({});
  const [rowActionId, setRowActionId] = useState<number | null>(null);
  const [pendingManagementAction, setPendingManagementAction] = useState<{ supplierId: number; action: "verify" | "reject" | "suspend" | "activate" } | null>(null);
  const [commissionSavingId, setCommissionSavingId] = useState<number | null>(null);
  const [supplierCommissionMap, setSupplierCommissionMap] = useState<Record<number, SupplierCommissionState>>({});
  const [rowCommissionRateDrafts, setRowCommissionRateDrafts] = useState<Record<number, string>>({});
  const [rowCommissionNoteDrafts, setRowCommissionNoteDrafts] = useState<Record<number, string>>({});
  const [exportingSuppliers, setExportingSuppliers] = useState(false);

  const [documents, setDocuments] = useState<SupplierDocumentRecord[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentStatusFilter, setDocumentStatusFilter] = useState<(typeof DOCUMENT_STATUS_OPTIONS)[number]>("all");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<number>>(new Set());
  const [documentReviewNotes, setDocumentReviewNotes] = useState<Record<number, string>>({});
  const [bulkDocumentNote, setBulkDocumentNote] = useState("");
  const [documentActionLoading, setDocumentActionLoading] = useState<number | null>(null);
  const [documentViewer, setDocumentViewer] = useState<SupplierDocumentRecord | null>(null);

  const [comparisonRows, setComparisonRows] = useState<SupplierComparisonRecord[]>([]);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonBarsVisible, setComparisonBarsVisible] = useState(false);

  const [activitySupplierId, setActivitySupplierId] = useState<number | null>(null);
  const [activityActionFilter, setActivityActionFilter] = useState("");
  const [activitySearch, setActivitySearch] = useState("");
  const [activityRows, setActivityRows] = useState<AuditLogRecord[]>([]);
  const [activityLoading, setActivityLoading] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<CreateSupplierFormState>({
    username: "",
    email: "",
    password: "",
    business_name: "",
    business_type: "individual",
    country: "",
    phone: "",
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");

  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importSummary, setImportSummary] = useState<{ created: number; failed: Array<{ identifier: string; message: string; password?: string }> } | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator"].includes(user?.role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, router, user]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPage(1);
      setSearchQuery(searchInput.trim());
    }, 250);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const supplierQuery = buildQueryString({
    page,
    page_size: pageSize,
    q: searchQuery || undefined,
    country: adminCountryCode,
    status: statusFilter,
    badge: badgeFilter,
    include_deleted: includeDeleted ? "true" : undefined,
  });

  const loadSuppliers = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!isLoggedIn) return;
      if (options?.silent) setRefreshing(true);
      else setLoading(true);

      try {
        const [response, commissionResponse] = await Promise.all([
          apiFetch(`/admin/suppliers/all${supplierQuery}`),
          apiFetch("/commission/suppliers"),
        ]);
        const payload = (await response.json().catch(() => null)) as SupplierListResponse | null;
        if (!response.ok) throw new Error((payload as { detail?: string } | null)?.detail || "Unable to load suppliers");
        const items = Array.isArray(payload?.items) ? payload.items : [];
        setSuppliers(items);
        setSummary(payload?.summary ?? { pending_suppliers: 0, active_suppliers: 0, suspended_suppliers: 0, total_revenue: 0 });
        setTotalSuppliers(payload?.total ?? 0);
        setTotalPages(payload?.total_pages ?? 1);
        if (!activitySupplierId && items.length > 0) setActivitySupplierId(items[0].id);
        if (commissionResponse.ok) {
          const commissionItems = (await commissionResponse.json()) as SupplierCommissionState[];
          const nextMap = commissionItems.reduce<Record<number, SupplierCommissionState>>((accumulator, item) => {
            accumulator[item.supplier_id] = item;
            return accumulator;
          }, {});
          setSupplierCommissionMap(nextMap);
        }
      } catch (error) {
        addToast(error instanceof Error ? error.message : "Unable to load suppliers", "error");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activitySupplierId, addToast, isLoggedIn, supplierQuery],
  );

  const loadDocuments = useCallback(async () => {
    if (!hasAdminPermission(role, "moderation.suppliers")) return;
    setDocumentsLoading(true);
    try {
      const response = await apiFetch(`/admin/suppliers/documents${buildQueryString({ status: documentStatusFilter === "all" ? undefined : documentStatusFilter })}`);
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error((payload as { detail?: string } | null)?.detail || "Unable to load supplier documents");
      setDocuments(normalizeListPage<SupplierDocumentRecord>(payload).data);
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to load supplier documents", "error");
    } finally {
      setDocumentsLoading(false);
    }
  }, [addToast, documentStatusFilter, role]);

  const loadComparison = useCallback(async () => {
    if (!hasAdminPermission(role, "analytics.view")) return;
    setComparisonLoading(true);
    try {
      const response = await apiFetch("/admin/suppliers/comparison");
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error((payload as { detail?: string } | null)?.detail || "Unable to load comparison data");
      setComparisonRows(normalizeListPage<SupplierComparisonRecord>(payload).data);
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to load comparison data", "error");
    } finally {
      setComparisonLoading(false);
    }
  }, [addToast, role]);

  const loadActivity = useCallback(async () => {
    if (!activitySupplierId || !hasAdminPermission(role, "audit.read")) return;
    setActivityLoading(true);
    try {
      const response = await apiFetch(
        `/admin/audit-logs${buildQueryString({
          page: 1,
          page_size: 30,
          resource_type: "user",
          resource_id: activitySupplierId,
          action: activityActionFilter || undefined,
          search: activitySearch || undefined,
        })}`,
      );
      const payload = (await response.json().catch(() => null)) as { items?: AuditLogRecord[]; detail?: string } | null;
      if (!response.ok) throw new Error(payload?.detail || "Unable to load supplier activity");
      setActivityRows(Array.isArray(payload?.items) ? payload.items : []);
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to load supplier activity", "error");
    } finally {
      setActivityLoading(false);
    }
  }, [activityActionFilter, activitySearch, activitySupplierId, addToast, role]);

  useEffect(() => {
    if (isLoggedIn) void loadSuppliers();
  }, [isLoggedIn, loadSuppliers]);

  useEffect(() => {
    if (currentSection === "documents") void loadDocuments();
  }, [currentSection, loadDocuments]);

  useEffect(() => {
    if (currentSection === "comparison") void loadComparison();
  }, [currentSection, loadComparison]);

  useEffect(() => {
    if (currentSection === "activity") void loadActivity();
  }, [currentSection, loadActivity]);

  const selectedSuppliers = useMemo(() => suppliers.filter((supplier) => selectedSupplierIds.has(supplier.id)), [selectedSupplierIds, suppliers]);
  const selectedDocuments = useMemo(() => documents.filter((document) => selectedDocumentIds.has(document.id)), [documents, selectedDocumentIds]);
  const supplierOptions = useMemo(
    () => suppliers.map((supplier) => ({ id: supplier.id, label: supplier.profile?.business_name || supplier.username })),
    [suppliers],
  );
  const comparisonTotalRevenue = useMemo(() => comparisonRows.reduce((sum, row) => sum + Number(row.revenue || 0), 0), [comparisonRows]);

  const changeSection = (section: SupplierSection) => {
    router.replace(`/admin/suppliers?section=${section}`, { scroll: false });
  };

  const toggleSupplierSelection = (supplierId: number) => {
    setSelectedSupplierIds((current) => {
      const next = new Set(current);
      if (next.has(supplierId)) next.delete(supplierId);
      else next.add(supplierId);
      return next;
    });
  };

  const handleSupplierAction = async (
    action: "verify" | "reject" | "suspend" | "activate" | "delete" | "badge",
    supplierIds: number[],
    options?: { note?: string; badgeLevel?: string },
  ) => {
    if (!supplierIds.length) return;
    if (action === "delete" && !window.confirm(`Archive ${supplierIds.length} supplier account(s)?`)) return;
    setBulkLoading(true);
    try {
      const response = await apiFetch("/admin/suppliers/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supplier_ids: supplierIds,
          action,
          note: (options?.note ?? bulkNote) || undefined,
          badge_level: options?.badgeLevel ?? (action === "badge" ? bulkBadgeLevel : undefined),
        }),
      });
      const payload = (await response.json().catch(() => ({}))) as { processed?: number; detail?: string };
      if (!response.ok) throw new Error(payload.detail || `Unable to ${action} suppliers`);
      addToast(`${payload.processed ?? supplierIds.length} supplier record(s) updated`, "success");
      if (supplierIds.length > 1) setSelectedSupplierIds(new Set());
      await loadSuppliers({ silent: true });
      if (currentSection === "activity") await loadActivity();
    } catch (error) {
      addToast(error instanceof Error ? error.message : `Unable to ${action} suppliers`, "error");
    } finally {
      setBulkLoading(false);
    }
  };

  const requestManagementAction = useCallback(
    async (supplierId: number, action: "verify" | "reject" | "suspend" | "activate") => {
      const eligibility = await canApprove("supplier");
      if (!eligibility.eligible) {
        setPendingManagementAction({ supplierId, action });
        return;
      }
      await handleSupplierAction(action, [supplierId]);
    },
    [canApprove, handleSupplierAction],
  );

  const confirmManagementAction = useCallback(
    async (supplierId: number, action: "verify" | "reject" | "suspend" | "activate", note?: string) => {
      await handleSupplierAction(action, [supplierId], { note: note || undefined });
    },
    [handleSupplierAction],
  );

  const refreshSupplierBadge = async (supplierId: number) => {
    setRowActionId(supplierId);
    try {
      const response = await apiFetch(`/admin/suppliers/${supplierId}/refresh-badge`, { method: "POST" });
      const payload = (await response.json().catch(() => ({}))) as { badge_level?: string; detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to refresh badge");
      addToast(`Credibility refreshed to ${payload.badge_level || "none"}`, "success");
      await loadSuppliers({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to refresh badge", "error");
    } finally {
      setRowActionId(null);
    }
  };

  const saveSupplierCommissionOverride = async (supplierId: number) => {
    const rateDraft = rowCommissionRateDrafts[supplierId];
    if (!rateDraft) return;
    setCommissionSavingId(supplierId);
    try {
      const response = await apiFetch(`/commission/suppliers/${supplierId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rate: Number(rateDraft) / 100,
          note: rowCommissionNoteDrafts[supplierId]?.trim() || null,
        }),
      });
      const payload = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to save supplier commission override");
      addToast("Supplier commission override saved", "success");
      await loadSuppliers({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to save supplier commission override", "error");
    } finally {
      setCommissionSavingId(null);
    }
  };

  const deleteSupplierCommissionOverride = async (supplierId: number) => {
    if (!window.confirm("Remove this supplier commission override and fall back to badge/default logic?")) return;
    setCommissionSavingId(supplierId);
    try {
      const response = await apiFetch(`/commission/suppliers/${supplierId}`, {
        method: "DELETE",
      });
      const payload = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to remove supplier commission override");
      addToast("Supplier commission override removed", "success");
      setRowCommissionRateDrafts((current) => {
        const next = { ...current };
        delete next[supplierId];
        return next;
      });
      setRowCommissionNoteDrafts((current) => {
        const next = { ...current };
        delete next[supplierId];
        return next;
      });
      await loadSuppliers({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to remove supplier commission override", "error");
    } finally {
      setCommissionSavingId(null);
    }
  };

  const restoreSupplier = async (supplierId: number) => {
    setRowActionId(supplierId);
    try {
      const response = await apiFetch(`/admin/suppliers/${supplierId}/restore`, { method: "POST" });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail || "Unable to restore supplier"); }
      addToast("Supplier restored", "success");
      await loadSuppliers({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to restore supplier", "error");
    } finally {
      setRowActionId(null);
    }
  };

  const bulkRestoreSuppliers = async () => {
    const ids = Array.from(selectedSupplierIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const response = await apiFetch("/admin/suppliers/bulk/restore", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids }),
      });
      const payload = (await response.json().catch(() => ({}))) as { processed?: number; detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to bulk restore suppliers");
      addToast(`${payload.processed ?? ids.length} supplier(s) restored`, "success");
      setSelectedSupplierIds(new Set());
      await loadSuppliers({ silent: true });
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to bulk restore suppliers", "error");
    } finally {
      setBulkLoading(false);
    }
  };

  const deleteSupplierAccounts = async (supplierIds: number[]) => {
    if (!supplierIds.length) return;
    const confirmLabel = supplierIds.length === 1 ? "this supplier account" : `${supplierIds.length} supplier accounts`;
    if (!window.confirm(`Permanently delete ${confirmLabel}? Accounts with preserved finance history will be skipped.`)) return;

    setBulkLoading(true);
    try {
      const response = await apiFetch("/admin/users/bulk", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: supplierIds }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { detail?: string };
        throw new Error(payload.detail || "Unable to delete supplier accounts");
      }

      const payload = (await response.json()) as BulkDeleteUsersResponse;
      const deletedCount = payload.deleted ?? 0;
      const skippedCount = payload.skipped ?? 0;
      const skipSummary = formatBulkDeleteSkipSummary(payload.skipped_details);

      setSelectedSupplierIds((current) => {
        const next = new Set(current);
        supplierIds.forEach((supplierId) => next.delete(supplierId));
        return next;
      });
      if (expandedSupplierId != null && supplierIds.includes(expandedSupplierId)) {
        setExpandedSupplierId(null);
      }

      await loadSuppliers({ silent: true });
      if (currentSection === "activity") await loadActivity();

      if (deletedCount > 0 && skippedCount === 0) {
        addToast(`${deletedCount} supplier account${deletedCount === 1 ? "" : "s"} deleted`, "success");
      } else if (deletedCount > 0) {
        addToast(
          `${deletedCount} supplier account${deletedCount === 1 ? "" : "s"} deleted. ${skippedCount} skipped${skipSummary ? `: ${skipSummary}` : ""}`,
          "warning",
        );
      } else if (skippedCount > 0) {
        addToast(`No supplier accounts deleted. ${skippedCount} skipped${skipSummary ? `: ${skipSummary}` : ""}`, "warning");
      } else {
        addToast("No supplier accounts deleted", "info");
      }
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to delete supplier accounts", "error");
    } finally {
      setBulkLoading(false);
    }
  };

  const reviewDocument = async (documentId: number, status: "approved" | "rejected", reviewNote?: string) => {
    setDocumentActionLoading(documentId);
    try {
      const response = await apiFetch(`/admin/suppliers/documents/${documentId}/review`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, review_note: reviewNote || undefined }),
      });
      const payload = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to review document");
      addToast(`Document ${status === "approved" ? "approved" : "rejected"}`, "success");
      await loadDocuments();
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to review document", "error");
    } finally {
      setDocumentActionLoading(null);
    }
  };

  const bulkReviewDocuments = async (status: "approved" | "rejected") => {
    if (!selectedDocuments.length) return;
    setDocumentActionLoading(-1);
    try {
      for (const document of selectedDocuments) {
        const response = await apiFetch(`/admin/suppliers/documents/${document.id}/review`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status, review_note: documentReviewNotes[document.id] || bulkDocumentNote || undefined }),
        });
        const payload = (await response.json().catch(() => ({}))) as { detail?: string };
        if (!response.ok) throw new Error(payload.detail || "Unable to update documents");
      }
      addToast(`${selectedDocuments.length} document(s) updated`, "success");
      setSelectedDocumentIds(new Set());
      await loadDocuments();
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to update documents", "error");
    } finally {
      setDocumentActionLoading(null);
    }
  };

  const handleCreateSupplier = async () => {
    setCreateLoading(true);
    setCreateError("");
    try {
      const response = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: createForm.username.trim(),
          email: createForm.email.trim().toLowerCase(),
          password: createForm.password,
          role: "supplier",
          business_name: createForm.business_name.trim(),
          business_type: createForm.business_type,
          country: createForm.country.trim() || undefined,
          phone: createForm.phone.trim() || undefined,
          terms_accepted: true,
        }),
      });
      const payload = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Unable to create supplier account");
      addToast("Supplier account created", "success");
      setShowCreateModal(false);
      setCreateForm({ username: "", email: "", password: "", business_name: "", business_type: "individual", country: "", phone: "" });
      await loadSuppliers({ silent: true });
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Unable to create supplier account");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleImportSuppliers = async () => {
    if (!importFile) return;
    setImportLoading(true);
    setImportSummary(null);
    try {
      const rows = parseCsvRows(await importFile.text());
      if (rows.length < 2) throw new Error("CSV must include a header row and at least one supplier row");
      const headers = rows[0].map((header) => header.toLowerCase());
      let created = 0;
      const failed: Array<{ identifier: string; message: string; password?: string }> = [];

      for (const row of rows.slice(1)) {
        const record = Object.fromEntries(headers.map((header, index) => [header, row[index] || ""])) as Record<string, string>;
        const identifier = record.email || record.username || `row-${created + failed.length + 2}`;
        const password = record.password || generateTemporaryPassword(identifier);
        const response = await apiFetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: record.username,
            email: record.email,
            password,
            role: "supplier",
            business_name: record.business_name,
            business_type: record.business_type || "individual",
            country: record.country || undefined,
            phone: record.phone || undefined,
            terms_accepted: true,
          }),
        });
        const payload = (await response.json().catch(() => ({}))) as { detail?: string };
        if (response.ok) created += 1;
        else failed.push({ identifier, message: payload.detail || "Registration failed", password: record.password ? undefined : password });
      }

      setImportSummary({ created, failed });
      if (created > 0) {
        addToast(`${created} supplier account(s) imported`, "success");
        await loadSuppliers({ silent: true });
      }
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to import suppliers", "error");
    } finally {
      setImportLoading(false);
    }
  };

  const exportSuppliers = async () => {
    setExportingSuppliers(true);
    try {
      const collected: SupplierRecord[] = [];
      let exportPage = 1;
      let exportTotalPages = 1;
      do {
        const response = await apiFetch(
          `/admin/suppliers/all${buildQueryString({ page: exportPage, page_size: 200, q: searchQuery || undefined, country: adminCountryCode, status: statusFilter, badge: badgeFilter })}`,
        );
        const payload = (await response.json().catch(() => null)) as SupplierListResponse | null;
        if (!response.ok) throw new Error((payload as { detail?: string } | null)?.detail || "Unable to export suppliers");
        collected.push(...(payload?.items ?? []));
        exportTotalPages = payload?.total_pages ?? 1;
        exportPage += 1;
      } while (exportPage <= exportTotalPages);

      downloadCsvFile(
        `supplier-management-${new Date().toISOString().slice(0, 10)}.csv`,
        collected.map((supplier) => ({
          supplier_id: supplier.id,
          username: supplier.username,
          business_name: supplier.profile?.business_name || "",
          email: supplier.email,
          status: statusForSupplier(supplier),
          badge_level: supplier.profile?.badge_level || "none",
          credibility_score: supplier.profile?.credibility_score || 0,
          product_count: supplier.product_count,
          order_count: supplier.order_count,
          revenue: supplier.revenue,
          joined: safeDate(supplier.created_at),
        })),
      );
      addToast(`Exported ${collected.length} supplier row(s)`, "success");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Unable to export suppliers", "error");
    } finally {
      setExportingSuppliers(false);
    }
  };

  const exportComparison = () => {
    if (!comparisonRows.length) return;
    downloadCsvFile(
      `supplier-comparison-${new Date().toISOString().slice(0, 10)}.csv`,
      comparisonRows.map((row) => ({
        supplier_id: row.id,
        supplier: row.username,
        email: row.email,
        products: row.product_count,
        orders: row.order_count,
        revenue: row.revenue,
        avg_price: row.avg_price,
        growth_rate: row.growth_rate ?? 0,
        revenue_share: row.revenue_share ?? (comparisonTotalRevenue ? (row.revenue / comparisonTotalRevenue) * 100 : 0),
      })),
    );
  };

  const exportActivity = () => {
    if (!activityRows.length) return;
    downloadCsvFile(
      `supplier-activity-${activitySupplierId || "all"}-${new Date().toISOString().slice(0, 10)}.csv`,
      activityRows.map((row) => ({
        id: row.id,
        actor: row.username || "system",
        actor_role: row.user_role || "-",
        action: row.action,
        status: row.status,
        created_at: safeDateTime(row.created_at),
        details: parseDetails(row.details),
      })),
    );
  };

  const { density } = useDensity();
  const cellPad = dc(density, "px-2 py-1.5", "px-3 py-2", "px-4 py-3");
  const bodyText = dc(density, "text-[11px]", "text-xs", "text-sm");

  const supplierColumns = useMemo<Array<EnterpriseColumn<SupplierRecord>>>(() => [
    {
      key: "id",
      label: "Supplier ID",
      width: "110px",
      sortable: true,
      sortValue: (supplier) => supplier.id,
      searchValue: (supplier) => `sup${supplier.id}`,
      render: (supplier) => <span className={`${bodyText} font-medium text-text`}>sup{supplier.id}</span>,
    },
    {
      key: "name",
      label: "Name",
      width: "250px",
      sortable: true,
      sortValue: (supplier) => (supplier.profile?.business_name || supplier.username).toLowerCase(),
      searchValue: (supplier) => `${supplier.profile?.business_name || ""} ${supplier.username} ${supplier.email}`,
      render: (supplier) => (
        <div>
          <div className="font-semibold text-text">{supplier.profile?.business_name || supplier.username}</div>
          <div className="mt-0.5 text-[11px] text-text-faint">@{supplier.username}</div>
        </div>
      ),
    },
    {
      key: "email",
      label: "Email",
      sortable: true,
      sortValue: (supplier) => supplier.email.toLowerCase(),
      searchValue: (supplier) => supplier.email,
      render: (supplier) => <span className={`${bodyText} text-text-muted`}>{supplier.email}</span>,
    },
    {
      key: "country",
      label: "Country / KYC",
      width: "140px",
      sortable: true,
      sortValue: (supplier) => supplier.profile?.country || "",
      searchValue: (supplier) => `${supplier.profile?.country || ""} ${supplier.profile?.verification_status || ""}`,
      render: (supplier) => (
        <div>
          <span className="text-xs font-medium text-text">{supplier.profile?.country || "—"}</span>
          {supplier.profile?.verification_status && (
            <span className={`ml-1.5 inline-flex items-center px-1 py-0.5 rounded text-[9px] font-semibold ${
              supplier.profile.verification_status === "verified" ? "bg-success/10 text-success" :
              supplier.profile.verification_status === "pending" ? "bg-warning/10 text-warning" :
              "bg-surface-3 text-text-muted"
            }`}>
              {supplier.profile.verification_status}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      width: "160px",
      sortable: true,
      sortValue: (supplier) => statusForSupplier(supplier),
      searchValue: (supplier) => statusForSupplier(supplier),
      render: (supplier) => {
        const supplierStatus = statusForSupplier(supplier);
        return <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize ${STATUS_TONE[supplierStatus] || "theme-chip-muted"}`}>{formatLabel(supplierStatus)}</span>;
      },
    },
    {
      key: "credibility",
      label: "Credibility",
      width: "180px",
      sortable: true,
      sortValue: (supplier) => Number(supplier.profile?.credibility_score || 0),
      searchValue: (supplier) => `${supplier.profile?.badge_level || "none"} ${supplier.profile?.credibility_score || 0}`,
      render: (supplier) => {
        const credibilityScore = Number(supplier.profile?.credibility_score || 0);
        return (
          <div className="min-w-32">
            <div className="mb-1 flex items-center justify-between gap-2 text-[11px]">
              <span className="font-semibold text-text">{credibilityScore}/100</span>
              <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${BADGE_TONE[supplier.profile?.badge_level || "none"] || "theme-chip-muted"}`}>{formatLabel(supplier.profile?.badge_level || "none")}</span>
            </div>
            <div className="h-2 rounded-full bg-surface-2"><div className="h-2 rounded-full bg-gradient-brand-to-success" style={{ width: `${Math.max(8, credibilityScore)}%` }} /></div>
          </div>
        );
      },
    },
    {
      key: "product_count",
      label: "Products",
      width: "100px",
      sortable: true,
      sortValue: (supplier) => supplier.product_count,
      searchValue: (supplier) => supplier.product_count,
      render: (supplier) => <span className={`${bodyText} font-semibold text-text`}>{supplier.product_count}</span>,
      align: "right",
    },
    {
      key: "order_count",
      label: "Orders",
      width: "100px",
      sortable: true,
      sortValue: (supplier) => supplier.order_count,
      searchValue: (supplier) => supplier.order_count,
      render: (supplier) => <span className={`${bodyText} font-semibold text-text`}>{supplier.order_count}</span>,
      align: "right",
    },
    {
      key: "revenue",
      label: "Revenue",
      width: "140px",
      sortable: true,
      sortValue: (supplier) => supplier.revenue,
      searchValue: (supplier) => supplier.revenue,
      render: (supplier) => <span className={`${bodyText} font-semibold text-text`}>{formatMoney(supplier.revenue)}</span>,
      align: "right",
    },
    {
      key: "created_at",
      label: "Joined",
      width: "120px",
      sortable: true,
      sortValue: (supplier) => new Date(supplier.created_at || 0).getTime(),
      searchValue: (supplier) => supplier.created_at || "",
      render: (supplier) => <span className={`${bodyText} text-text-muted`}>{safeDate(supplier.created_at)}</span>,
    },
  ], [bodyText, formatMoney]);

  if (authLoading) return null;

  return (
    <>
      <AdminLayout title="Suppliers" headerMode="compact">
        <PanelContent width="full" className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard icon={ShieldCheck} label="Pending approvals" value={String(summary.pending_suppliers)} hint="Suppliers waiting for moderation" />
            <StatCard icon={CheckCircle2} label="Active suppliers" value={String(summary.active_suppliers)} hint="Live supplier accounts" />
            <StatCard icon={XCircle} label="Suspended suppliers" value={String(summary.suspended_suppliers)} hint="Accounts paused by admin" />
            <StatCard icon={ArrowDownUp} label="Revenue contribution" value={formatMoney(summary.total_revenue)} hint="Supplier-attributed order value" />
          </div>

          <div className="theme-card rounded-xl border p-3">
            <div className="mb-3 flex flex-wrap items-center justify-end gap-2">
              <button onClick={() => setShowCreateModal(true)} className="theme-btn-primary inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold">
                <Plus className="h-3.5 w-3.5" /> Add Supplier
              </button>
              <button onClick={() => setShowImportModal(true)} className="theme-btn-secondary inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted">
                <Upload className="h-3.5 w-3.5" /> Import CSV
              </button>
              <button onClick={() => void exportSuppliers()} disabled={exportingSuppliers} className="theme-btn-secondary inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
                {exportingSuppliers ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />} Export CSV
              </button>
              <button onClick={() => void loadSuppliers({ silent: true })} disabled={refreshing} className="theme-btn-secondary inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">
                <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>
            <div className="grid gap-2 xl:grid-cols-[minmax(0,1fr)_200px_200px_auto]">
              <label className="relative block">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-faint" />
                <input
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder="Search by supplier name, email, or business name"
                  className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs focus:border-primary focus:outline-none"
                />
              </label>
              <select value={statusFilter} onChange={(event) => { setPage(1); setStatusFilter(event.target.value as (typeof STATUS_OPTIONS)[number]); }} className="theme-input rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none">
                {STATUS_OPTIONS.map((option) => <option key={option} value={option}>{formatLabel(option)}</option>)}
              </select>
              <select value={badgeFilter} onChange={(event) => { setPage(1); setBadgeFilter(event.target.value as (typeof BADGE_FILTER_OPTIONS)[number]); }} className="theme-input rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none">
                {BADGE_FILTER_OPTIONS.map((option) => <option key={option} value={option}>{option === "all" ? "All badges" : formatLabel(option)}</option>)}
              </select>
              {selectedCountry && selectedCountry.code !== "*" ? (
                <div className="flex items-center gap-1.5 rounded-xl border border-primary/20 bg-primary/5 px-3 py-2 text-xs font-medium text-primary">
                  <span>{selectedCountry.name} ({selectedCountry.code})</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted">
                  All countries
                </div>
              )}
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={includeDeleted} onChange={(e) => { setPage(1); setIncludeDeleted(e.target.checked); }} className="rounded border-border" />
                <span className="text-[11px] text-text-muted whitespace-nowrap">Show deleted</span>
              </label>
            </div>
            <PanelTabs items={SECTION_OPTIONS} value={currentSection} onChange={changeSection} className="mt-3 border-0 bg-transparent p-0" />
          </div>

          {currentSection === "management" && (
            <div className="space-y-4">
              <div className="theme-card rounded-xl border p-3">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
                  <span>{totalSuppliers} supplier accounts{selectedSupplierIds.size > 0 ? ` · ${selectedSupplierIds.size} selected` : ""}</span>
                  <div className="flex gap-2">
                    <button onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page <= 1} className="theme-btn-secondary rounded-lg border px-3 py-1.5 text-xs font-semibold text-text-muted disabled:opacity-50">Previous</button>
                    <button onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages} className="theme-btn-secondary rounded-lg border px-3 py-1.5 text-xs font-semibold text-text-muted disabled:opacity-50">Next</button>
                  </div>
                </div>

                <EnterpriseDataTable
                  columns={supplierColumns}
                  rows={suppliers}
                  rowKey={(supplier) => supplier.id}
                  densityMode={density}
                  initialRowsPerPage={pageSize}
                  rowsPerPageOptions={[pageSize]}
                  enableBulkActions
                  enableExport={false}
                  enableGlobalSearch={false}
                  selectedRowKeys={Array.from(selectedSupplierIds)}
                  onSelectedRowKeysChange={(keys) => setSelectedSupplierIds(new Set(keys.map((key) => Number(key))))}
                  emptyState={loading ? "Loading suppliers..." : "No suppliers matched the current filters."}
                  expandedRowKey={expandedSupplierId ?? undefined}
                  rowActions={(supplier) => {
                    const supplierStatus = statusForSupplier(supplier);
                    const isExpanded = expandedSupplierId === supplier.id;
                    const badgeValue = rowBadgeDrafts[supplier.id] || supplier.profile?.badge_level || "none";
                    if (supplier.is_deleted) {
                      return (
                        <div className="flex flex-wrap items-center justify-end gap-1.5">
                          <button onClick={() => void restoreSupplier(supplier.id)} disabled={rowActionId === supplier.id} className="rounded-md border border-success/30 px-2 py-1 text-[11px] font-semibold text-success disabled:opacity-50">
                            <RotateCcw className="mr-1 inline h-3 w-3" />Restore
                          </button>
                        </div>
                      );
                    }
                    return (
                      <div className="flex flex-wrap items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            setExpandedSupplierId(isExpanded ? null : supplier.id);
                            setActivitySupplierId(supplier.id);
                          }}
                          className="theme-btn-secondary rounded-md border px-2 py-1 text-[11px] font-semibold text-text-muted"
                        >
                          {isExpanded ? "Hide Details" : "Details"}
                        </button>
                        {supplierStatus === "pending" ? <button onClick={() => void requestManagementAction(supplier.id, "verify")} disabled={bulkLoading} className="theme-chip-success rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50">Approve</button> : null}
                        {supplierStatus !== "approved" && supplierStatus !== "rejected" ? <button onClick={() => void requestManagementAction(supplier.id, "reject")} disabled={bulkLoading} className="theme-chip-danger rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50">Reject</button> : null}
                        <button onClick={() => void requestManagementAction(supplier.id, Boolean(supplier.is_active) ? "suspend" : "activate")} disabled={bulkLoading} className="theme-btn-secondary rounded-md border px-2 py-1 text-[11px] font-semibold text-text-muted disabled:opacity-50">{Boolean(supplier.is_active) ? "Suspend" : "Reactivate"}</button>
                        <select aria-label={`Badge for supplier ${supplier.username}`} value={badgeValue} onChange={(event) => setRowBadgeDrafts((current) => ({ ...current, [supplier.id]: event.target.value }))} className="theme-input w-28 rounded-md border px-2 py-1 text-[11px]">
                          {BADGE_ASSIGN_OPTIONS.map((option) => <option key={option} value={option}>{formatLabel(option)}</option>)}
                        </select>
                        <button onClick={() => void handleSupplierAction("badge", [supplier.id], { badgeLevel: badgeValue })} disabled={bulkLoading} className="theme-btn-primary rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50">Save badge</button>
                        {role === "admin" ? <Button variant="danger" className="rounded-md px-2 py-1 text-[11px] font-semibold text-danger disabled:opacity-50" onClick={() => void deleteSupplierAccounts([supplier.id])} disabled={bulkLoading}>Delete</Button> : null}
                        <button onClick={() => void handleSupplierAction("delete", [supplier.id])} disabled={bulkLoading || role !== "admin"} className="rounded-md border border-danger/20 px-2 py-1 text-[11px] font-semibold text-danger disabled:opacity-50">Archive</button>
                      </div>
                    );
                  }}
                  expandedRowRenderer={(supplier) => {
                    const commissionState = supplierCommissionMap[supplier.id] ?? null;
                    const commissionRateDraft = rowCommissionRateDrafts[supplier.id]
                      ?? (commissionState ? (commissionState.current_rate * 100).toFixed(2) : "");
                    const commissionNoteDraft = rowCommissionNoteDrafts[supplier.id] ?? "";
                    const hasActiveCommissionOverride = Boolean(commissionState?.history?.some((entry) => entry.is_active));

                    return (
                      <div className="p-4">
                        <div className="mb-3 flex items-center justify-between gap-3">
                          <div>
                            <h4 className="text-sm font-bold text-text">Supplier Details</h4>
                            <p className="mt-1 text-xs text-text-muted">Expanded supplier context for {supplier.profile?.business_name || supplier.username}.</p>
                          </div>
                          <button type="button" onClick={() => setExpandedSupplierId(null)} className="rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
                            Close
                          </button>
                        </div>
                        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                          {[
                            ["Business ID", supplier.profile?.tax_id || "Encrypted / unavailable"],
                            ["Phone", supplier.profile?.phone_business || supplier.phone || "-"],
                            ["Top product", supplier.top_product_name || "No sales data yet"],
                            ["Website", supplier.profile?.website || "-"],
                            ["Verification note", supplier.verification_note || "No note recorded"],
                          ].map(([label, value]) => (
                            <div key={String(label)} className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">{label}</p>
                              <p className="mt-1.5 text-xs font-medium text-text">{value}</p>
                            </div>
                          ))}
                          <div className="rounded-xl border border-border bg-surface-1 p-3 md:col-span-2 xl:col-span-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Commission Override</p>
                                <p className="mt-1 text-xs text-text-muted">Manage the supplier-side commission component here instead of the commission page.</p>
                              </div>
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="rounded-full bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text">Supplier {commissionState ? `${(commissionState.current_rate * 100).toFixed(2)}%` : "—"}</span>
                                <span className="rounded-full bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text">Default combined {commissionState?.combined_default_rate != null ? `${(commissionState.combined_default_rate * 100).toFixed(2)}%` : "—"}</span>
                                <span className="rounded-full bg-surface-2 px-2.5 py-1 text-[11px] font-semibold capitalize text-text-muted">{commissionState?.calculation_method || "global"}</span>
                              </div>
                            </div>
                            <div className="mt-3 grid gap-2 lg:grid-cols-[160px_minmax(0,1fr)_auto]">
                              <label>
                                <span className="mb-1 block text-[11px] font-semibold text-text">Override Rate (%)</span>
                                <input
                                  type="number"
                                  step="0.01"
                                  value={commissionRateDraft}
                                  onChange={(event) => setRowCommissionRateDrafts((current) => ({ ...current, [supplier.id]: event.target.value }))}
                                  className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                                />
                              </label>
                              <label>
                                <span className="mb-1 block text-[11px] font-semibold text-text">Note</span>
                                <input
                                  value={commissionNoteDraft}
                                  onChange={(event) => setRowCommissionNoteDrafts((current) => ({ ...current, [supplier.id]: event.target.value }))}
                                  placeholder="Negotiation reason or approval note"
                                  className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                                />
                              </label>
                              <div className="flex items-end gap-2">
                                <button
                                  onClick={() => void saveSupplierCommissionOverride(supplier.id)}
                                  disabled={commissionSavingId === supplier.id || !commissionRateDraft}
                                  className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50"
                                >
                                  {commissionSavingId === supplier.id ? "Saving..." : "Save Override"}
                                </button>
                                {hasActiveCommissionOverride ? (
                                  <button
                                    onClick={() => void deleteSupplierCommissionOverride(supplier.id)}
                                    disabled={commissionSavingId === supplier.id}
                                    className="rounded-xl border border-danger/20 px-3 py-2 text-xs font-semibold text-danger disabled:opacity-50"
                                  >
                                    Remove Override
                                  </button>
                                ) : null}
                              </div>
                            </div>
                            <p className="mt-2 text-[11px] text-text-muted">
                              Supplier overrides replace the badge-derived supplier component before the engine adds the product/category/global base rate.
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  }}
                />

                <div className="mt-3 flex items-center justify-between text-xs text-text-muted">
                  <span>Page {page} of {totalPages}</span>
                  <span>{suppliers.length} visible on this page</span>
                </div>
              </div>
            </div>
          )}

          {currentSection === "documents" && (
            <div className="space-y-4">
              <div className="theme-card rounded-xl border p-3">
                <div className="grid gap-2 xl:grid-cols-[200px_minmax(0,1fr)_160px_160px]">
                  <select value={documentStatusFilter} onChange={(event) => setDocumentStatusFilter(event.target.value as (typeof DOCUMENT_STATUS_OPTIONS)[number])} className="theme-input rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none">
                    {DOCUMENT_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{option === "all" ? "All document states" : formatLabel(option)}</option>)}
                  </select>
                  <input value={bulkDocumentNote} onChange={(event) => setBulkDocumentNote(event.target.value)} placeholder="Reviewer note for bulk KYC decisions" className="theme-input rounded-xl border px-3 py-2 text-xs focus:border-primary focus:outline-none" />
                  <button onClick={() => void bulkReviewDocuments("approved")} disabled={!selectedDocumentIds.size || documentActionLoading !== null} className="theme-chip-success rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">Bulk approve</button>
                  <button onClick={() => void bulkReviewDocuments("rejected")} disabled={!selectedDocumentIds.size || documentActionLoading !== null} className="theme-chip-danger rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">Bulk reject</button>
                </div>
              </div>

              <div className="theme-card overflow-hidden rounded-xl border">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-270 text-xs">
                    <thead>
                      <tr className="border-b border-border bg-surface-2/40">
                        <th className="px-3 py-2 text-left"><input type="checkbox" aria-label="Select all supplier documents" checked={documents.length > 0 && documents.every((document) => selectedDocumentIds.has(document.id))} onChange={() => setSelectedDocumentIds((current) => { const next = new Set(current); const allSelected = documents.length > 0 && documents.every((document) => next.has(document.id)); documents.forEach((document) => { if (allSelected) next.delete(document.id); else next.add(document.id); }); return next; })} className="h-3.5 w-3.5 rounded accent-primary" /></th>
                        {["Supplier", "Document", "Type", "Status", "Submitted", "Audit trail", "Actions"].map((heading) => <th key={heading} className={`${cellPad} text-left text-[11px] font-semibold uppercase tracking-wide text-text-faint`}>{heading}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {documentsLoading ? (
                        Array.from({ length: 6 }).map((_, index) => <tr key={`document-skeleton-${index}`} className="border-b border-border/60"><td colSpan={7} className={cellPad}><div className="h-10 animate-pulse rounded-xl bg-surface-2" /></td></tr>)
                      ) : documents.length === 0 ? (
                        <tr><td colSpan={7} className="p-8 text-center text-xs text-text-muted">No supplier documents matched the current filter.</td></tr>
                      ) : (
                        documents.map((document) => (
                          <tr key={document.id} className="border-b border-border/60 hover:bg-surface-1/60">
                            <td className="px-3 py-2"><input type="checkbox" aria-label={`Select document ${document.document_name}`} checked={selectedDocumentIds.has(document.id)} onChange={() => setSelectedDocumentIds((current) => { const next = new Set(current); if (next.has(document.id)) next.delete(document.id); else next.add(document.id); return next; })} className="h-3.5 w-3.5 rounded accent-primary" /></td>
                            <td className={`${cellPad} ${bodyText} font-medium text-text`}>{document.supplier_username || `Supplier ${document.supplier_id}`}</td>
                            <td className="px-3 py-2">
                              <button onClick={() => setDocumentViewer(document)} className="font-semibold text-primary hover:underline">{document.document_name}</button>
                              <input value={documentReviewNotes[document.id] || ""} onChange={(event) => setDocumentReviewNotes((current) => ({ ...current, [document.id]: event.target.value }))} placeholder="Review note" className="theme-input mt-1.5 w-full rounded-xl border px-2 py-1.5 text-[11px]" />
                            </td>
                            <td className={`${cellPad} ${bodyText} text-text-muted`}>{formatLabel(document.document_type)}</td>
                            <td className={cellPad}><span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${STATUS_TONE[document.status] || "theme-chip-muted"}`}>{formatLabel(document.status)}</span></td>
                            <td className={`${cellPad} ${bodyText} text-text-muted`}>{safeDate(document.created_at)}</td>
                            <td className={`${cellPad} ${bodyText} text-text-muted`}>Reviewed by {document.reviewed_by || "-"}<br />{safeDateTime(document.reviewed_at)}</td>
                            <td className={cellPad}><div className="flex flex-wrap gap-1.5"><button onClick={() => void reviewDocument(document.id, "approved", documentReviewNotes[document.id])} disabled={documentActionLoading !== null} className="theme-chip-success rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50">Approve</button><button onClick={() => void reviewDocument(document.id, "rejected", documentReviewNotes[document.id])} disabled={documentActionLoading !== null} className="theme-chip-danger rounded-md px-2 py-1 text-[11px] font-semibold disabled:opacity-50">Reject</button></div></td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {currentSection === "comparison" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-text">Supplier comparison matrix</h2>
                  <p className="text-xs text-text-muted">Compare contribution, average catalog price, and growth without loading chart-heavy widgets by default.</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => void loadComparison()} disabled={comparisonLoading} className="theme-btn-secondary rounded-xl border px-3 py-1.5 text-xs font-semibold text-text-muted disabled:opacity-50"><RefreshCw className={`mr-1.5 inline h-3.5 w-3.5 ${comparisonLoading ? "animate-spin" : ""}`} /> Refresh</button>
                  <button onClick={exportComparison} disabled={!comparisonRows.length} className="theme-btn-primary rounded-xl px-3 py-1.5 text-xs font-semibold disabled:opacity-50">Export KPI CSV</button>
                </div>
              </div>

              <div className="theme-card overflow-hidden rounded-xl border">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-245 text-xs">
                    <thead><tr className="border-b border-border bg-surface-2/40">{["Supplier", "Products", "Orders", "Revenue", "Avg price", "Growth rate", "Revenue share", "Joined"].map((heading) => <th key={heading} className={`${cellPad} text-left text-[11px] font-semibold uppercase tracking-wide text-text-faint`}>{heading}</th>)}</tr></thead>
                    <tbody>
                      {comparisonLoading ? (
                        Array.from({ length: 5 }).map((_, index) => <tr key={`compare-skeleton-${index}`} className="border-b border-border/60"><td colSpan={8} className="px-3 py-2"><div className="h-10 animate-pulse rounded-xl bg-surface-2" /></td></tr>)
                      ) : comparisonRows.length === 0 ? (
                        <tr><td colSpan={8} className="p-8 text-center text-xs text-text-muted">No comparison data is available yet.</td></tr>
                      ) : (
                        comparisonRows.map((row) => {
                          const revenueShare = row.revenue_share ?? (comparisonTotalRevenue ? (row.revenue / comparisonTotalRevenue) * 100 : 0);
                          const growthRate = row.growth_rate ?? 0;
                          return <tr key={row.id} className="border-b border-border/60 hover:bg-surface-1/60"><td className="px-3 py-2"><div className="font-semibold text-text">{row.username}</div><div className="text-[11px] text-text-faint">{row.email}</div></td><td className="px-3 py-2 font-semibold text-text">{row.product_count}</td><td className="px-3 py-2 font-semibold text-text">{row.order_count}</td><td className="px-3 py-2 font-semibold text-text">{formatMoney(row.revenue)}</td><td className="px-3 py-2 text-text-muted">{formatMoney(row.avg_price)}</td><td className="px-3 py-2"><span className={`font-semibold ${growthRate >= 0 ? "text-success" : "text-danger"}`}>{growthRate.toFixed(2)}%</span></td><td className="px-3 py-2 text-text-muted">{revenueShare.toFixed(2)}%</td><td className="px-3 py-2 text-text-muted">{safeDate(row.joined)}</td></tr>;
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="theme-card rounded-xl border p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-xs font-semibold text-text">Revenue contribution bars</h3>
                    <p className="text-xs text-text-muted">Bars render only when requested, so the section stays light by default.</p>
                  </div>
                  <button onClick={() => setComparisonBarsVisible((current) => !current)} className="theme-btn-secondary rounded-xl border px-3 py-1.5 text-xs font-semibold text-text-muted">{comparisonBarsVisible ? "Hide bars" : "Load bars"}</button>
                </div>
                {comparisonBarsVisible && <div className="mt-3 space-y-2">{comparisonRows.slice(0, 12).map((row) => { const revenueShare = row.revenue_share ?? (comparisonTotalRevenue ? (row.revenue / comparisonTotalRevenue) * 100 : 0); return <div key={`bar-${row.id}`} className="grid gap-2 md:grid-cols-[200px_minmax(0,1fr)_80px] md:items-center"><div className="text-xs font-medium text-text">{row.username}</div><div className="h-3 overflow-hidden rounded-full bg-surface-2"><motion.div initial={{ width: 0 }} animate={{ width: `${Math.max(5, revenueShare)}%` }} className="h-3 rounded-full bg-gradient-brand-to-success" /></div><div className="text-right text-[11px] font-semibold text-text-muted">{revenueShare.toFixed(2)}%</div></div>; })}</div>}
              </div>
            </div>
          )}

          {currentSection === "badges" && (
            <div className="space-y-4">
              <div className="theme-card rounded-xl border p-3">
                <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_300px]">
                  <div>
                    <h2 className="text-base font-bold text-text">Badge operations</h2>
                    <p className="mt-0.5 text-xs text-text-muted">Select suppliers from the management table, then apply a credibility badge or trigger score recalculation here.</p>
                    <div className="mt-3 flex flex-wrap gap-1.5"><span className="rounded-full bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text-muted">{selectedSupplierIds.size} selected supplier(s)</span>{selectedSuppliers.slice(0, 5).map((supplier) => <span key={supplier.id} className="rounded-full bg-surface-2 px-2.5 py-1 text-[11px] font-semibold text-text">{supplier.profile?.business_name || supplier.username}</span>)}</div>
                  </div>
                  <div className="rounded-xl border border-border bg-surface-1 p-3">
                    <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Selected badge</label>
                    <select value={bulkBadgeLevel} onChange={(event) => setBulkBadgeLevel(event.target.value as (typeof BADGE_ASSIGN_OPTIONS)[number])} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">{BADGE_ASSIGN_OPTIONS.map((option) => <option key={option} value={option}>{formatLabel(option)}</option>)}</select>
                    <div className="mt-2.5 grid gap-2 sm:grid-cols-2">
                      <button onClick={() => void handleSupplierAction("badge", Array.from(selectedSupplierIds), { badgeLevel: bulkBadgeLevel })} disabled={!selectedSupplierIds.size || bulkLoading} className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">Assign badge</button>
                      <button onClick={() => void Promise.all(Array.from(selectedSupplierIds).map(async (supplierId) => refreshSupplierBadge(supplierId)))} disabled={!selectedSupplierIds.size || bulkLoading} className="theme-btn-secondary rounded-xl border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">Recalculate</button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="theme-card overflow-hidden rounded-xl border">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-215 text-xs">
                    <thead><tr className="border-b border-border bg-surface-2/40">{["Supplier", "Current badge", "Credibility score", "Products", "Orders", "Revenue", "Quick action"].map((heading) => <th key={heading} className={`${cellPad} text-left text-[11px] font-semibold uppercase tracking-wide text-text-faint`}>{heading}</th>)}</tr></thead>
                    <tbody>
                      {suppliers.map((supplier) => { const badgeValue = rowBadgeDrafts[supplier.id] || supplier.profile?.badge_level || "none"; return <tr key={`badge-${supplier.id}`} className="border-b border-border/60 hover:bg-surface-1/60"><td className="px-3 py-2 font-semibold text-text">{supplier.profile?.business_name || supplier.username}</td><td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${BADGE_TONE[supplier.profile?.badge_level || "none"] || "theme-chip-muted"}`}>{formatLabel(supplier.profile?.badge_level || "none")}</span></td><td className="px-3 py-2 font-semibold text-text">{Number(supplier.profile?.credibility_score || 0)}/100</td><td className="px-3 py-2 text-text-muted">{supplier.product_count}</td><td className="px-3 py-2 text-text-muted">{supplier.order_count}</td><td className="px-3 py-2 text-text-muted">{formatMoney(supplier.revenue)}</td><td className="px-3 py-2"><div className="flex flex-wrap gap-1.5"><select value={badgeValue} onChange={(event) => setRowBadgeDrafts((current) => ({ ...current, [supplier.id]: event.target.value }))} className="theme-input rounded-md border px-2 py-1 text-[11px]">{BADGE_ASSIGN_OPTIONS.map((option) => <option key={option} value={option}>{formatLabel(option)}</option>)}</select><button onClick={() => void handleSupplierAction("badge", [supplier.id], { badgeLevel: badgeValue })} className="theme-btn-primary rounded-md px-2 py-1 text-[11px] font-semibold">Save</button><button onClick={() => void refreshSupplierBadge(supplier.id)} className="theme-btn-secondary rounded-md border px-2 py-1 text-[11px] font-semibold text-text-muted">Recalculate</button></div></td></tr>; })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {currentSection === "activity" && (
            <div className="space-y-4">
              <div className="theme-card rounded-xl border p-3">
                <div className="grid gap-2 xl:grid-cols-[240px_180px_minmax(0,1fr)_140px_140px]">
                  <select value={activitySupplierId || ""} onChange={(event) => setActivitySupplierId(Number(event.target.value) || null)} className="theme-input rounded-xl border px-3 py-2 text-xs"><option value="">Select supplier</option>{supplierOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select>
                  <input value={activityActionFilter} onChange={(event) => setActivityActionFilter(event.target.value)} placeholder="Action type" className="theme-input rounded-xl border px-3 py-2 text-xs" />
                  <input value={activitySearch} onChange={(event) => setActivitySearch(event.target.value)} placeholder="Search actor or details" className="theme-input rounded-xl border px-3 py-2 text-xs" />
                  <button onClick={() => void loadActivity()} disabled={!activitySupplierId || activityLoading} className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">Load</button>
                  <button onClick={exportActivity} disabled={!activityRows.length} className="theme-btn-secondary rounded-xl border px-3 py-2 text-xs font-semibold text-text-muted disabled:opacity-50">Export</button>
                </div>
              </div>

              <div className="theme-card overflow-hidden rounded-xl border">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-230 text-xs">
                    <thead><tr className="border-b border-border bg-surface-2/40">{["Timestamp", "Actor", "Role", "Action", "Status", "Details"].map((heading) => <th key={heading} className={`${cellPad} text-left text-[11px] font-semibold uppercase tracking-wide text-text-faint`}>{heading}</th>)}</tr></thead>
                    <tbody>
                      {activityLoading ? (
                        Array.from({ length: 6 }).map((_, index) => <tr key={`activity-skeleton-${index}`} className="border-b border-border/60"><td colSpan={6} className="px-3 py-2"><div className="h-10 animate-pulse rounded-xl bg-surface-2" /></td></tr>)
                      ) : activityRows.length === 0 ? (
                        <tr><td colSpan={6} className="p-8 text-center text-xs text-text-muted">Choose a supplier and load activity to review the immutable moderation trail.</td></tr>
                      ) : (
                        activityRows.map((row) => <tr key={row.id} className="border-b border-border/60 hover:bg-surface-1/60"><td className="px-3 py-2 text-text-muted">{safeDateTime(row.created_at)}</td><td className="px-3 py-2 font-semibold text-text">{row.username || "system"}</td><td className="px-3 py-2 text-text-muted">{row.user_role || "-"}</td><td className="px-3 py-2 font-semibold text-text">{row.action}</td><td className="px-3 py-2"><span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${row.status === "success" ? "theme-chip-success" : "theme-chip-warning"}`}>{formatLabel(row.status)}</span></td><td className="px-3 py-2 text-text-muted">{parseDetails(row.details)}</td></tr>)
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </PanelContent>
      </AdminLayout>

      <BulkActionBar selectedCount={selectedSupplierIds.size} onClearSelection={() => setSelectedSupplierIds(new Set())} actions={[{ label: "Approve Selected", onClick: () => void handleSupplierAction("verify", Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "success" }, { label: "Reject Selected", onClick: () => void handleSupplierAction("reject", Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "danger" }, { label: "Suspend Selected", onClick: () => void handleSupplierAction("suspend", Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "warning" }, { label: "Reactivate Selected", onClick: () => void handleSupplierAction("activate", Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "primary" }, { label: "Assign Badge", onClick: () => void handleSupplierAction("badge", Array.from(selectedSupplierIds), { badgeLevel: bulkBadgeLevel }), loading: bulkLoading, variant: "primary" }, ...(role === "admin" ? [{ label: "Delete Selected", onClick: () => void deleteSupplierAccounts(Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "danger" as const }, { label: "Archive Selected", onClick: () => void handleSupplierAction("delete", Array.from(selectedSupplierIds)), loading: bulkLoading, variant: "danger" as const }, { label: "Restore Selected", onClick: () => void bulkRestoreSuppliers(), loading: bulkLoading, variant: "success" as const }] : [])]}>
        <input value={bulkNote} onChange={(event) => setBulkNote(event.target.value)} placeholder="Reason" className="theme-input w-36 rounded-xl border px-3 py-1.5 text-xs" />
        <select value={bulkBadgeLevel} onChange={(event) => setBulkBadgeLevel(event.target.value as (typeof BADGE_ASSIGN_OPTIONS)[number])} className="theme-input rounded-xl border px-3 py-1.5 text-xs">{BADGE_ASSIGN_OPTIONS.map((option) => <option key={option} value={option}>{formatLabel(option)}</option>)}</select>
      </BulkActionBar>

      <ApprovalActionModal
        isOpen={!!pendingManagementAction}
        resourceType="supplier"
        resourceLabel={pendingManagementAction ? `#${pendingManagementAction.supplierId}` : undefined}
        action={pendingManagementAction?.action || "verify"}
        onClose={() => setPendingManagementAction(null)}
        onConfirm={async (options) => { if (!pendingManagementAction) return; await confirmManagementAction(pendingManagementAction.supplierId, pendingManagementAction.action, options?.note); }}
      />

      <AnimatePresence>
        {showCreateModal && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4" onClick={(event: React.MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setShowCreateModal(false)}><motion.div initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 16, opacity: 0 }} className="theme-card w-full max-w-2xl rounded-2xl border p-6 shadow-card-xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Quick onboarding</p><h2 className="mt-1.5 text-xl font-bold text-text">Create supplier account</h2><p className="mt-1 text-xs text-text-muted">Minimal fields for fast onboarding.</p></div><button onClick={() => setShowCreateModal(false)} className="rounded-xl p-2 text-text-faint hover:bg-surface-2 hover:text-text"><X className="h-5 w-5" /></button></div><div className="mt-4 grid gap-2.5 md:grid-cols-2"><input value={createForm.username} onChange={(event) => setCreateForm((current) => ({ ...current, username: event.target.value }))} placeholder="Username" className="theme-input rounded-xl border px-3 py-2 text-xs" /><input type="email" value={createForm.email} onChange={(event) => setCreateForm((current) => ({ ...current, email: event.target.value }))} placeholder="Email" className="theme-input rounded-xl border px-3 py-2 text-xs" /><input value={createForm.business_name} onChange={(event) => setCreateForm((current) => ({ ...current, business_name: event.target.value }))} placeholder="Business name" className="theme-input rounded-xl border px-3 py-2 text-xs" /><input type="password" value={createForm.password} onChange={(event) => setCreateForm((current) => ({ ...current, password: event.target.value }))} placeholder="Temporary password" className="theme-input rounded-xl border px-3 py-2 text-xs" /><select value={createForm.business_type} onChange={(event) => setCreateForm((current) => ({ ...current, business_type: event.target.value }))} className="theme-input rounded-xl border px-3 py-2 text-xs"><option value="individual">Individual</option><option value="company">Company</option><option value="partnership">Partnership</option><option value="llc">LLC</option></select><input value={createForm.country} onChange={(event) => setCreateForm((current) => ({ ...current, country: event.target.value }))} placeholder="Country" className="theme-input rounded-xl border px-3 py-2 text-xs" /></div>{createError && <div className="theme-alert-danger mt-3 flex items-start gap-2 rounded-xl p-3 text-xs"><AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {createError}</div>}<div className="mt-4 flex flex-wrap justify-end gap-2"><button onClick={() => setShowCreateModal(false)} className="theme-btn-secondary rounded-xl border px-3 py-2 text-xs font-semibold text-text-muted">Cancel</button><button onClick={handleCreateSupplier} disabled={createLoading || !createForm.username || !createForm.email || !createForm.password || !createForm.business_name} className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">{createLoading ? "Creating..." : "Create supplier"}</button></div></motion.div></motion.div>}
      </AnimatePresence>

      <AnimatePresence>
        {showImportModal && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4" onClick={(event: React.MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setShowImportModal(false)}><motion.div initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 16, opacity: 0 }} className="theme-card w-full max-w-3xl rounded-2xl border p-6 shadow-card-xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Mass onboarding</p><h2 className="mt-1.5 text-xl font-bold text-text">Import supplier CSV</h2><p className="mt-1 texxs text-text-muted">Headers: username, email, business_name, password, business_type, country, phone.</p></div><button onClick={() => setShowImportModal(false)} className="rounded-xl p-2 text-text-faint hover:bg-surface-2 hover:text-text"><X className="h-5 w-5" /></button></div><label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-border bg-surface-1 px-6 py-10 text-center text-xs text-text-muted"><FileUp className="mb-22 h-6 w-6 text-text-faint" /><span className="font-semibold text-text">Choose a CSV file</span><input type="file" accept=".csv,text/csv" className="hidden" onChange={(event) => setImportFile(event.target.files?.[0] || null)} /></label>{importFile && <p className="mt-3 text-xs text-text">Selected file: <span className="font-semibold">{importFile.name}</span></p>}{importSummary && <div className="mt-3 rounded-xl border border-border bg-surface-1 p-3"><p className="text-xs font-semibold text-text">{importSummary.created} supplier account(s) created</p>{importSummary.failed.length > 0 && <div className="mt-2 space-y-1.5 text-[11px] text-text-muted">{importSummary.failed.slice(0, 8).map((entry) => <div key={`${entry.identifier}-${entry.message}`} className="rounded-xl bg-surface-2 px-2.5 py-1.5"><div className="font-semibold text-text">{entry.identifier}</div><div>{entry.message}</div>{entry.password && <div>Generated password: {entry.password}</div>}</div>)}</div>}</div>}<div className="mt-4 flex flex-wrap justify-end gap-2"><button onClick={() => setShowImportModal(false)} className="theme-btn-secondary rounded-xl border px-3 py-2 text-xs font-semibold text-text-muted">Close</button><button onClick={handleImportSuppliers} disabled={!importFile || importLoading} className="theme-btn-primary rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50">{importLoading ? "Importing..." : "Start import"}</button></div></motion.div></motion.div>}
      </AnimatePresence>

      <AnimatePresence>
        {documentViewer && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="theme-overlay fixed inset-0 z-50 flex items-center justify-center p-4" onClick={(event: React.MouseEvent<HTMLDivElement>) => event.target === event.currentTarget && setDocumentViewer(null)}><motion.div initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 16, opacity: 0 }} className="theme-card flex h-[80vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border shadow-card-xl"><div className="flex items-center justify-between border-b border-border px-6 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Document viewer</p><h3 className="mt-1 text-lg font-bold text-text">{documentViewer.document_name}</h3></div><button onClick={() => setDocumentViewer(null)} className="rounded-xl p-2 text-text-faint hover:bg-surface-2 hover:text-text"><X className="h-5 w-5" /></button></div><div className="min-h-0 flex-1 bg-surface-2 p-4">{documentViewer.file_url.match(/\.(png|jpg|jpeg|gif|webp)$/i) ? <img src={documentViewer.file_url} alt={documentViewer.document_name} className="h-full w-full rounded-xl bg-white object-contain" /> : <iframe src={documentViewer.file_url} title={documentViewer.document_name} className="h-full w-full rounded-xl bg-white" />}</div></motion.div></motion.div>}
      </AnimatePresence>
    </>
  );
}

export default function AdminSuppliersPage() {
  return (
    <Suspense>
      <AdminSuppliersInner />
    </Suspense>
  );
}
